import asyncio
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from async_asgi_testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.settings import settings
from tests.functional.utils import fake, create_database, drop_database


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client(event_loop) -> TestClient:
    async with TestClient(app) as client:
        client.headers = {
            "Host": "0.0.0.0",
            "Content-Type": "application/json",
            "x-request-id": fake.cryptographic.uuid(),
        }
        yield client


@pytest.fixture(scope="session")
def init_database():
    base_dir = Path(__file__).resolve().parent.parent.parent
    alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
    return lambda *args, **kwargs: command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
async def database(event_loop, init_database):
    await create_database(settings.DB.DSN)

    engine = create_async_engine(settings.DB.DSN)
    async with engine.begin() as conn:
        await conn.run_sync(init_database)
    await engine.dispose()

    try:
        yield settings.DB.DSN
    finally:
        await drop_database(settings.DB.DSN)


@pytest.fixture(scope="session")
async def sqla_engine(database):
    engine = create_async_engine(database)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture()
async def db_session(mocker: MockerFixture, sqla_engine):
    """
    Fixture that returns a SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.
    """
    connection = await sqla_engine.connect()
    trans = await connection.begin()

    Session = sessionmaker(connection, expire_on_commit=False, class_=AsyncSession)
    session = Session()

    mocker.patch("sqlalchemy.orm.session.sessionmaker.__call__", return_value=session)

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()

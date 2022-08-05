import pytest
from fastapi import status
from fastapi.security import HTTPBasicCredentials
from pytest_mock import MockerFixture

from app.api.dependencies import auth
from app.main import app
from app.settings import settings

pytestmark = pytest.mark.asyncio

VALID_CREDENTIALS = (
    settings.SECURITY.BASIC_AUTH.USERNAME,
    settings.SECURITY.BASIC_AUTH.PASSWD,
)
INVALID_CREDENTIALS = ("invalid username", "invalid password")


@pytest.fixture
def mocked_basic_auth(request, mocker: MockerFixture) -> None:
    username, password = request.param
    auth_obj = HTTPBasicCredentials(username=username, password=password)

    dependency_overrides = {auth.security: lambda: auth_obj}
    mocker.patch.object(app, "dependency_overrides", dependency_overrides)


@pytest.mark.parametrize(
    "url_path,mocked_basic_auth,expected_code",
    [
        (app.url_path_for("get_swagger"), VALID_CREDENTIALS, status.HTTP_200_OK),
        (app.url_path_for("get_redoc"), VALID_CREDENTIALS, status.HTTP_200_OK),
        (app.url_path_for("get_openapi_json"), VALID_CREDENTIALS, status.HTTP_200_OK),
        (
            app.url_path_for("get_swagger"),
            INVALID_CREDENTIALS,
            status.HTTP_401_UNAUTHORIZED,
        ),
        (
            app.url_path_for("get_redoc"),
            INVALID_CREDENTIALS,
            status.HTTP_401_UNAUTHORIZED,
        ),
        (
            app.url_path_for("get_openapi_json"),
            INVALID_CREDENTIALS,
            status.HTTP_401_UNAUTHORIZED,
        ),
    ],
    indirect=["mocked_basic_auth"],
)
async def test_basic_auth(client, url_path, mocked_basic_auth, expected_code):
    response = await client.get(path=url_path)
    assert response.status_code == expected_code, response.text

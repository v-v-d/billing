from typing import Any

import pytest
from jose import jwt

from app.settings import settings
from tests.functional.utils import fake


@pytest.fixture
def valid_admin_payload() -> dict[str, Any]:
    return {
        "user_id": fake.cryptographic.uuid(),
        "login": fake.person.full_name(),
        "email": fake.person.email(),
        "is_admin": True,
        "roles": ["admin"],
    }


@pytest.fixture
def valid_admin_token(valid_admin_payload) -> str:
    token = jwt.encode(
        valid_admin_payload,
        settings.SECURITY.JWT_AUTH.SECRET_KEY,
        algorithm=settings.SECURITY.JWT_AUTH.ALGORITHM,
    )

    return f"Bearer {token}"

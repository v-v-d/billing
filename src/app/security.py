import secrets

from fastapi.security import HTTPBasicCredentials
from jose import JWTError, jwt
from pydantic import ValidationError

from app.api.schemas import ORJSONModel
from app.settings import settings


class BaseSecurityError(Exception):
    pass


class NotAuthenticatedError(BaseSecurityError):
    pass


class TokenData(ORJSONModel):
    user_id: str
    login: str
    email: str
    roles: list[str]


def verify_basic_auth_credentials(credentials: HTTPBasicCredentials) -> None:
    correct_username = secrets.compare_digest(
        credentials.username, settings.SECURITY.BASIC_AUTH.USERNAME
    )
    correct_password = secrets.compare_digest(
        credentials.password, settings.SECURITY.BASIC_AUTH.PASSWD
    )
    if not (correct_username and correct_password):
        raise NotAuthenticatedError


def decode_jwt_token(token: str) -> TokenData:
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECURITY.JWT_AUTH.SECRET_KEY,
            algorithms=[settings.SECURITY.JWT_AUTH.ALGORITHM],
        )
    except JWTError:
        raise NotAuthenticatedError

    try:
        return TokenData(**decoded_token)
    except ValidationError:
        raise NotAuthenticatedError

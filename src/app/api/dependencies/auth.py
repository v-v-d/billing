import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from urllib.parse import unquote

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer

from app.api.errors import NOT_AUTHENTICATED, NOT_ALLOWED, INCORRECT_CREDENTIALS
from app.security import (
    TokenData,
    decode_jwt_token,
    verify_basic_auth_credentials,
    NotAuthenticatedError,
)

security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class SignatureValidator:
    def __init__(self, secret_key: str, signature_expiration_hours: int):
        self.secret_key = secret_key
        self.signature_expiration_hours = signature_expiration_hours

    def __call__(self, signature: str, date: str) -> None:
        unquoted_signature = unquote(signature)
        unquoted_date = unquote(date)

        parsed_date = datetime.fromisoformat(unquoted_date)

        if parsed_date < datetime.utcnow() - timedelta(
            hours=self.signature_expiration_hours
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=NOT_AUTHENTICATED
            )

        to_hash = bytes(unquoted_date, "utf-8")
        secret = bytes(self.secret_key, "utf-8")

        valid_signature = base64.b64encode(
            hmac.new(secret, to_hash, digestmod=hashlib.sha256).digest()
        ).decode()

        if unquoted_signature != valid_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=NOT_AUTHENTICATED
            )


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    try:
        verify_basic_auth_credentials(credentials)
    except NotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_CREDENTIALS,
            headers={"WWW-Authenticate": "Basic"},
        )


async def decode_jwt(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        return decode_jwt_token(token)
    except NotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=NOT_AUTHENTICATED,
        )


async def check_admin_role(token_data: TokenData = Depends(decode_jwt)) -> None:
    if "admin" not in token_data.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=NOT_ALLOWED,
        )

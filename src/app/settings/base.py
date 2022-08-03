from pathlib import Path

from pydantic import (
    BaseSettings,
    AnyHttpUrl,
    RedisDsn,
    validator,
    AnyUrl,
    PostgresDsn,
    Field,
)


class UvicornSettings(BaseSettings):
    app: str = "app.main:app"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 3

    class Config:
        env_prefix = "UVICORN_"


class SecuritySettings(BaseSettings):
    class JWTAuthSettings(BaseSettings):
        SECRET_KEY: str
        ALGORITHM: str

        class Config:
            env_prefix = "SECURITY_JWT_AUTH_"

    class BasicAuthSettings(BaseSettings):
        USERNAME: str
        PASSWD: str

        class Config:
            env_prefix = "SECURITY_BASIC_AUTH_"

    ALLOWED_HOSTS: list[str]
    JWT_AUTH: JWTAuthSettings = JWTAuthSettings()
    BASIC_AUTH: BasicAuthSettings = BasicAuthSettings()

    class Config:
        env_prefix = "SECURITY_"


class APMSettings(BaseSettings):
    ENABLED: bool
    SERVER_URL: AnyHttpUrl
    SERVICE_NAME: str
    ENVIRONMENT: str

    class Config:
        env_prefix = "APM_"


class BackoffSettings(BaseSettings):
    MAX_TIME_SEC: int

    class Config:
        env_prefix = "BACKOFF_"


class SentrySettings(BaseSettings):
    DSN: str
    ENVIRONMENT: str
    ENABLED: bool = True
    DEBUG: bool = False
    SAMPLE_RATE: float = 1.0

    class Config:
        env_prefix = "SENTRY_"


class BaseDSNSettings(BaseSettings):
    USER: str = ""
    PASSWORD: str = ""
    HOST: str = ""
    PORT: int = 0
    PROTOCOL: str = ""
    PATH: str = ""
    DSN: AnyUrl = None

    @validator("DSN", pre=True)
    def build_dsn(cls, v, values) -> str:
        if v:
            return v

        protocol = values["PROTOCOL"]
        user = values["USER"]
        passwd = values["PASSWORD"]
        host = values["HOST"]
        port = values["PORT"]
        path = values["PATH"]

        if user and passwd:
            if path:
                return f"{protocol}://{user}:{passwd}@{host}:{port}/{path}"

            return f"{protocol}://{user}:{passwd}@{host}:{port}"

        if path:
            return f"{protocol}://{host}:{port}/{path}"

        return f"{protocol}://{host}:{port}"


class RedisSettings(BaseDSNSettings):
    HOST: str
    PORT: int
    PROTOCOL: str = "redis"
    DSN: RedisDsn = None

    class Config:
        env_prefix = "REDIS_"


class DatabaseSettings(BaseDSNSettings):
    HOST: str
    PORT: int
    PROTOCOL: str = "postgresql+asyncpg"
    PATH: str = Field(..., env="POSTGRES_DB")
    SCHEMA: str = "content"
    POOL_RECYCLE: int = 1800
    DSN: PostgresDsn = None

    class Config:
        env_prefix = "POSTGRES_"


class LoggingSettings(BaseSettings):
    JSON_ENABLED: bool = True
    FILES_ENABLED: bool = True
    DEFAULT_LEVEL: str = "INFO"
    DIR: Path = Path("/code/shared", "logs")

    class Config:
        env_prefix = "LOGGING_"


class AuthIntegrationSettings(BaseSettings):
    BASE_URL: AnyHttpUrl
    TIMEOUT_SEC: int = 10
    USERS_PER_PAGE: int = 5

    class Config:
        env_prefix = "AUTH_INTEGRATION_"


class AdminIntegrationSettings(BaseSettings):
    BASE_URL: AnyHttpUrl
    TIMEOUT_SEC: int = 10
    USERS_PER_PAGE: int = 5

    class Config:
        env_prefix = "ADMIN_INTEGRATION_"


class BankIntegrationSettings(BaseSettings):
    BASE_URL: AnyHttpUrl
    TIMEOUT_SEC: int = 10
    USERS_PER_PAGE: int = 5

    class Config:
        env_prefix = "BANK_INTEGRATION_"


class FiscalIntegrationSettings(BaseSettings):
    BASE_URL: AnyHttpUrl
    TIMEOUT_SEC: int = 10
    USERS_PER_PAGE: int = 5

    class Config:
        env_prefix = "FISCAL_INTEGRATION_"


class BackgroundTasksSettings(BaseSettings):
    class SubscriptionTaskSettings(BaseSettings):
        DEFER_SEC: int = 60 * 1
        MAX_TRIES: int = (3 * 60 * 60) / DEFER_SEC  # 3 hours

        class Config:
            env_prefix = "BACKGROUND_SUBSCRIPTION_"

    class ReceiptTaskSettings(BaseSettings):
        DEFER_SEC: int = 60 * 15
        MAX_TRIES: int = (3 * 24 * 60 * 60) / DEFER_SEC  # 3 days

        class Config:
            env_prefix = "BACKGROUND_RECEIPT_"

    SUBSCRIPTION: SubscriptionTaskSettings = SubscriptionTaskSettings()
    RECEIPT: ReceiptTaskSettings = ReceiptTaskSettings()

    class Config:
        env_prefix = "BACKGROUND_"


class CommonSettings(BaseSettings):
    PROJECT_NAME: str = "billing-app"
    OPENAPI_URL: str = "/api/docs/openapi.json"

    DEBUG: bool = False

    UVICORN: UvicornSettings = UvicornSettings()
    SECURITY: SecuritySettings = SecuritySettings()
    APM: APMSettings = APMSettings()
    BACKOFF: BackoffSettings = BackoffSettings()
    SENTRY: SentrySettings = SentrySettings()
    REDIS: RedisSettings = RedisSettings()
    DB: DatabaseSettings = DatabaseSettings()
    LOGS: LoggingSettings = LoggingSettings()
    AUTH_INTEGRATION: AuthIntegrationSettings = AuthIntegrationSettings()
    ADMIN_INTEGRATION: AdminIntegrationSettings = AdminIntegrationSettings()
    BANK_INTEGRATION: BankIntegrationSettings = BankIntegrationSettings()
    FISCAL_INTEGRATION: FiscalIntegrationSettings = FiscalIntegrationSettings()
    BACKGROUND: BackgroundTasksSettings = BackgroundTasksSettings()

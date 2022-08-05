from arq.connections import RedisSettings

from app.settings import settings

redis_settings = RedisSettings.from_dsn(settings.REDIS.DSN)

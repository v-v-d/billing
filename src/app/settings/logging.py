from pathlib import Path

from app.settings import settings

LOGGING = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(funcName)s - %(message)s"
        },
        "json": {
            "()": "app.logging.ServiceJsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
        },
        "uvicorn.access": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
        "uvicorn.error": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "default",
        },
        "elasticapm": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "formatter": "default",
        },
        "transactions": {
            "class": "logging.StreamHandler",
            "level": settings.LOGS.DEFAULT_LEVEL,
            "formatter": "default",
        },
        "receipts": {
            "class": "logging.StreamHandler",
            "level": settings.LOGS.DEFAULT_LEVEL,
            "formatter": "default",
        },
        "sentry": {
            "class": "logging.StreamHandler",
            "level": settings.LOGS.DEFAULT_LEVEL,
            "formatter": "default",
        },
    },
    "loggers": {
        "uvicorn.access": {
            "handlers": ["console", "uvicorn.access"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "uvicorn.error"],
            "level": "ERROR",
            "propagate": False,
        },
        "elasticapm": {
            "handlers": ["console", "elasticapm"],
            "level": "WARNING",
            "propagate": False,
        },
        "app.services.transactions": {
            "handlers": ["console", "transactions"],
            "level": settings.LOGS.DEFAULT_LEVEL,
            "propagate": False,
        },
        "app.services.receipts": {
            "handlers": ["console", "receipts"],
            "level": settings.LOGS.DEFAULT_LEVEL,
            "propagate": False,
        },
        "app.sentry": {
            "handlers": ["console", "sentry"],
            "level": settings.LOGS.DEFAULT_LEVEL,
            "propagate": False,
        },
    },
    "root": {"level": "DEBUG", "handlers": ["console"]},
}

if settings.LOGS.JSON_ENABLED:
    LOGGING["handlers"]["console"]["formatter"] = "json"
    LOGGING["handlers"]["console"]["stream"] = "ext://sys.stdout"

if settings.LOGS.FILES_ENABLED:
    for handler_name, handler in LOGGING["handlers"]:
        if handler_name == "console":
            continue

        handler["class"] = "logging.handlers.RotatingFileHandler"
        handler["filename"] = (
            Path(settings.LOGS.DIR / f"{handler_name}.log").as_posix(),
        )
        handler["maxBytes"] = 1024**3 * 10
        handler["backupCount"] = 10

from pythonjsonlogger import jsonlogger

from app.context import ctx
from app.settings import settings


class ServiceJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["service_name"] = settings.PROJECT_NAME
        log_record.update(ctx.get().dict())

from loguru import logger
from sentry_sdk import add_breadcrumb


def breadcrumb_sink(message):
    record = message.record
    add_breadcrumb(category=record["name"], message=record["message"], level=record["level"].name)


logger.add(breadcrumb_sink)

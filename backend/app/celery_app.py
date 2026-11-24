import os
from urllib.parse import quote

from celery import Celery


def _broker_url() -> str:
    """Адрес RabbitMQ: готовый CELERY_BROKER_URL или сборка из RABBITMQ_*."""
    url = os.getenv("CELERY_BROKER_URL")

    if url:
        return url

    user = quote(os.getenv("RABBITMQ_USER", "guest"), safe="")
    password = quote(os.getenv("RABBITMQ_PASSWORD", "guest"), safe="")
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = os.getenv("RABBITMQ_PORT", "5672")

    return f"amqp://{user}:{password}@{host}:{port}//"


celery_app = Celery(
    "job_tracker",
    broker=_broker_url(),
    include=["app.tasks"],
)

celery_app.conf.update(
    # Не зависать надолго, если RabbitMQ недоступен
    broker_connection_timeout=2,
    broker_connection_retry_on_startup=True,
)

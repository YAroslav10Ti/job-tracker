import os

from celery import Celery

RABBITMQ_USER = os.getenv("RABBITMQ_USER", "jobtracker")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "jobtracker_password")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")

broker_url = (
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}"
    f"@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"
)

celery_app = Celery(
    "job_tracker",
    broker=broker_url,
    include=["app.tasks"],
)
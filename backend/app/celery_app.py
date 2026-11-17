from celery import Celery

celery_app = Celery(
    "job_tracker",
    broker="amqp://jobtracker:jobtracker_password@rabbitmq:5672//",
    include=["app.tasks"],
)
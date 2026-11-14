from celery import Celery

celery_app = Celery(
    "job_tracker",
    broker="redis://redis:6379/1",
    include=["app.tasks"], 
)
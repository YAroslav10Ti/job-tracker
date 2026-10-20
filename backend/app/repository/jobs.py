from app.schemas import JobResponse
from app.models import Job


def get_job_repository(job_id: int, db) -> JobResponse:
    return db.query(Job).filter(Job.id == job_id).first()

def create_job_repository(new_job: Job, db) -> JobResponse:
    db.add(new_job)
    return new_job

def get_jobs_repository(db) -> list[JobResponse]:
    return db.query(Job).all()


def delete_job_repository(job: Job, db) -> JobResponse:
    db.delete(job)
    return job
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import JobCreate, JobResponse, JobUpdate
from app.models import Job
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repository.jobs import get_job_repository, create_job_repository, get_jobs_repository, delete_job_repository


def create_job_service(payload: JobCreate, db: Session) -> JobResponse:
    # создать новую запись о вакансии
    new_job = Job(
        company=payload.company,
        position=payload.position,
        url=payload.url,
        status=payload.status,
        notes=payload.notes
    )

    try:
        # сохранить ее в базу данных
        create_job_repository(new_job, db)
        db.commit()
        db.refresh(new_job)
        return new_job
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create job")




def get_jobs_service(db: Session) -> list[JobResponse]:
    return get_jobs_repository(db)


def get_job_service(job_id: int, db: Session) -> JobResponse:
    current_job = get_job_repository(job_id, db)

    if current_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return current_job


def update_job_service(job_id: int, payload: JobUpdate, db: Session) -> JobResponse:
    current_job = get_job_repository(job_id, db)
    if current_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    new_data = payload.model_dump(exclude_unset=True)

    for key, value in new_data.items():
        setattr(current_job, key, value)

    try:
        db.commit()
        db.refresh(current_job)
        return current_job
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update job")


def delete_job_service(job_id: int, db: Session) -> JobResponse:
    current_job = get_job_repository(job_id, db)
    if current_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    delete_job_repository(current_job, db)
    try:
        db.commit()
        return current_job
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete job")








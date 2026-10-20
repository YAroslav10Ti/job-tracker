from fastapi import status, APIRouter
from app.schemas import JobCreate, JobResponse, JobUpdate
from app.database import get_db
from fastapi import Depends
from app.services.jobs import create_job_service, get_jobs_service, get_job_service, update_job_service, delete_job_service


router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"],
)

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db = Depends(get_db)) -> JobResponse:
    return create_job_service(payload, db)


@router.get("/", response_model=list[JobResponse])
def get_jobs(db = Depends(get_db)) -> list[JobResponse]:
    return get_jobs_service(db)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db = Depends(get_db)) -> JobResponse:
    return get_job_service(job_id, db)


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, payload: JobUpdate, db = Depends(get_db)) -> JobResponse:
    return update_job_service(job_id, payload, db)



@router.delete("/{job_id}", response_model=JobResponse)
def delete_job(job_id: int, db = Depends(get_db)) -> JobResponse:
    return delete_job_service(job_id, db)
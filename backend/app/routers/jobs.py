from fastapi import status, APIRouter
from app.schemas import JobCreate, JobResponse, JobUpdate, UserCreateLogin, UserResponse, UserLoginResponse
from app.database import get_db
from fastapi import Depends
from app.services.jobs import create_job_service, get_jobs_service, get_job_service, update_job_service, delete_job_service, create_user, login_new_user, change_password_services, delete_user_services
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Job
from app.dependencies.auth import get_authenticated_user


router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"], 
)




@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user)) -> Job:
    return await create_job_service(payload, db, current_user.id)

@router.get("/", response_model=list[JobResponse])
async def get_jobs(db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user), search: str | None = None) -> list[Job]:
    return await get_jobs_service(db, current_user.id, search)






@router.post("/register")
async def register_user(payload: UserCreateLogin, db: AsyncSession = Depends(get_db)) -> UserResponse:
    return await create_user(payload, db)  


@router.post("/login")
async def login_user(payload: UserCreateLogin, db: AsyncSession = Depends(get_db)) -> UserLoginResponse:
    return await login_new_user(payload, db)


@router.patch("/update")
async def change_password(payload: UserCreateLogin, db: AsyncSession = Depends(get_db)) -> UserLoginResponse:
    return await change_password_services(payload, db) 


@router.delete("/me")
async def delete_user(db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user)) -> dict:
    await delete_user_services(current_user, db)
    return {"message": "User deleted successfully"}







@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user)) -> Job:
    return await get_job_service(job_id, db, current_user.id)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, payload: JobUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user)) -> Job:
    return await update_job_service(job_id, payload, db, current_user.id)


@router.delete("/{job_id}", response_model=JobResponse)
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_authenticated_user)) -> Job:
    return await delete_job_service(job_id, db, current_user.id)


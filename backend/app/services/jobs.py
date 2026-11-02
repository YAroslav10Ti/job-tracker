from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import JobCreate, JobUpdate, UserCreateLogin, UserResponse, UserLoginResponse
from app.models import Job
from app.repository.jobs import (
    get_job_repository,
    create_job_repository,
    get_jobs_repository,
    delete_job_repository,
    get_job_by_name_repository,
    get_current_user,
    create_new_user,
    reset_new_password, 
    delete_user_repository
)

from app.security import verify_password, create_access_token
from app.security import hash_password


async def create_job_service(payload: JobCreate, db: AsyncSession, id: int) -> Job:
    # создать новую запись о вакансии
    new_job = Job(
        company=payload.company,
        position=payload.position,
        url=payload.url,
        status=payload.status,
        last_date=payload.last_date,
        notes=payload.notes,
        user_id=id
    )

    try:
        # сохранить ее в базу данных
        create_job_repository(new_job, db)
        await db.commit()
        await db.refresh(new_job)
        return new_job
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create job")


async def get_jobs_service(db: AsyncSession, id: int, search: str | None = None) -> list[Job]:
    if search:
        return await get_job_by_name_repository(db, id, search)
    else:
        return await get_jobs_repository(db, id)


async def get_job_service(job_id: int, db: AsyncSession, id: int) -> Job:
    current_job =  await get_job_repository(job_id, db, id)

    if current_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return current_job


async def update_job_service(job_id: int, payload: JobUpdate, db: AsyncSession, id: int) -> Job:
    current_job = await get_job_repository(job_id, db, id)
    if current_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    new_data = payload.model_dump(exclude_unset=True)

    for key, value in new_data.items():
        setattr(current_job, key, value)

    try:
        await db.commit()
        await db.refresh(current_job)
        return current_job
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update job")


async def delete_job_service(job_id: int, db: AsyncSession, id: int) -> Job:
    current_job = await get_job_repository(job_id, db, id)
    if current_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        await delete_job_repository(current_job, db)
        await db.commit()
        return current_job
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete job")




async def create_user(payload: UserCreateLogin, db: AsyncSession) -> UserResponse:
    current_user = await get_current_user(payload.email, db)

    if current_user is not None:
        raise HTTPException(status_code=400, detail="User is already exist")
    
    try:
        new_user = await create_new_user(payload, db)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user") 




async def login_new_user(payload: UserCreateLogin, db: AsyncSession) -> UserLoginResponse:
    current_user = await get_current_user(payload.email, db)

    if current_user is None:
        raise HTTPException(status_code=400, detail="User is not exist")

    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is wrong")

    access_token = create_access_token(current_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


async def change_password_services(payload: UserCreateLogin, db: AsyncSession) -> UserLoginResponse:
    current_user = await get_current_user(payload.email, db)

    if current_user is None:
        raise HTTPException(status_code=400, detail="User is not exist")

    hashed_password = hash_password(payload.password)

    await reset_new_password(current_user, hashed_password, db)

    access_token = create_access_token(current_user.id)

    try:
        await db.commit()
        await db.refresh(current_user)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to change password")

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }



async def delete_user_services(payload: UserCreateLogin, db: AsyncSession) -> dict:
    current_user = await get_current_user(payload.email, db)

    if current_user is None:
        raise HTTPException(status_code=400, detail="User is not exist")

    try:
        await delete_user_repository(current_user, db)
        await db.commit()
        return {"message": "User deleted successfully"}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user")

    

    
    
    


        








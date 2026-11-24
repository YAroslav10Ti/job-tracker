
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, User
from app.schemas import UserCreateLogin
from app.security import hash_password


# Получить одну вакансию конкретного пользователя
async def get_job_repository(
    job_id: int,
    db: AsyncSession,
    id: int
) -> Job | None:
    result = await db.execute(
        select(Job).where(
            Job.id == job_id,
            Job.user_id == id
        )
    )
    return result.scalar_one_or_none()


# Создать вакансию
def create_job_repository(
    new_job: Job,
    db: AsyncSession
) -> Job:
    db.add(new_job)
    return new_job


# Получить все вакансии конкретного пользователя
async def get_jobs_repository(
    db: AsyncSession,
    id: int
) -> list[Job]:
    result = await db.execute(
        select(Job).where(
            Job.user_id == id
        )
    )
    return list(result.scalars().all())


# Найти вакансии по названию должности конкретного пользователя
async def get_job_by_name_repository(
    db: AsyncSession,
    id: int,
    search: str
) -> list[Job]:
    result = await db.execute(
        select(Job).where(
            Job.position.ilike(f"%{search}%"),
            Job.user_id == id
        )
    )
    return list(result.scalars().all())


# Удалить вакансию
async def delete_job_repository(
    job: Job,
    db: AsyncSession
) -> Job:
    await db.delete(job)
    return job


# Найти пользователя по email
async def get_current_user(
    email: str,
    db: AsyncSession
) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


# Создать нового пользователя
async def create_new_user(
    new_user: UserCreateLogin,
    db: AsyncSession
) -> User:
    user = User(
        email=new_user.email,
        hashed_password=hash_password(new_user.password)
    )

    db.add(user)
    return user



async def reset_new_password(
    user: User,
    hashed_password: str,
    db: AsyncSession
) -> User:
    user.hashed_password = hashed_password
    db.add(user)
    return user


async def delete_user_repository(
    user: User,
    db: AsyncSession
) -> User:
    await db.delete(user)
    return user




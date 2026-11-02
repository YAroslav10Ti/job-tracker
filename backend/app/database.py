import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set")

ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://",
    "postgresql+asyncpg://",
)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

SessionLocal = async_sessionmaker(bind=engine, autocommit=False, autoflush=False)

async def get_db():
    async with SessionLocal() as db:
        yield db
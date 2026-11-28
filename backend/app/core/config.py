
import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

REDIS_URL = os.getenv("REDIS_URL")
REDIS_STATISTICS_URL = os.getenv("REDIS_STATISTICS_URL")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY must be at least 32 characters")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL is not set")

if not REDIS_STATISTICS_URL:
    raise RuntimeError("REDIS_STATISTICS_URL is not set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

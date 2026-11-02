
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession

import jwt

from app.core.config import SECRET_KEY, ALGORITHM
from app.database import get_db
from app.models import User


# Получение Bearer-токена из заголовка Authorization
bearer_scheme = HTTPBearer()


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Извлекаем токен
        token = credentials.credentials

        # Проверяем подпись и срок действия токена
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        # Получаем ID пользователя из токена
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    # Ищем пользователя в базе данных
    user = await db.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


JobStatus = Literal[
    "Заинтересован",
    "Подана заявка",
    "Собеседование",
    "Отклонена",
]


def _validate_http_url(value: str | None) -> str | None:
    """Пустая ссылка -> None, иначе только http/https и не длиннее 2048 символов."""
    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    if len(value) > 2048:
        raise ValueError("URL is too long")

    if not value.lower().startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    return value


class JobBase(BaseModel):
    company: str = Field(min_length=1, max_length=100)
    position: str = Field(min_length=1, max_length=150)
    url: str | None = None
    status: JobStatus = "Заинтересован"
    last_date: str = Field(default="Неизвестно", max_length=100)
    notes: str = Field(default="", max_length=5000)


class JobCreate(JobBase):
    @field_validator("url")
    @classmethod
    def check_url(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


# В ответе ссылку не проверяем: в базе могут лежать старые записи
class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class JobUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=100)
    position: str | None = Field(default=None, min_length=1, max_length=150)
    url: str | None = None
    status: JobStatus | None = None
    last_date: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("url")
    @classmethod
    def check_url(cls, value: str | None) -> str | None:
        return _validate_http_url(value)


class UserCreateLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # A@x.com и a@x.com - один и тот же пользователь
        return value.strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

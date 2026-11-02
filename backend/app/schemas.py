from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


JobStatus = Literal[
    "Заинтересован",
    "Подана заявка",
    "Собеседование",
    "Отклонена", 
] 


class JobCreate(BaseModel):
    company: str = Field(min_length=1, max_length=100)
    position: str = Field(min_length=1, max_length=150)
    url: str | None = None
    status: JobStatus = "Заинтересован"
    last_date: str = Field(default="Неизвестно", max_length=100)
    notes: str = Field(default="", max_length=5000)


class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class JobUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=100)
    position: str | None = Field(default=None, min_length=1, max_length=150)
    url: str | None = None
    status: JobStatus | None = None
    last_date: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=5000)


class UserCreateLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    notes: str = Field(default="", max_length=5000)


class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class JobUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=100)
    position: str | None = Field(default=None, min_length=1, max_length=150)
    url: str | None = None
    status: JobStatus | None = None
    notes: str | None = Field(default=None, max_length=5000)

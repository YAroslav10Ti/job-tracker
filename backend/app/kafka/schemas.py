# создаем схему для событий, которые будут публиковаться в Kafka


from datetime import datetime, timezone 
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class JobEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)

    event_type: str

    user_id: int

    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    data: dict
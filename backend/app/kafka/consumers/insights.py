
import asyncio
import logging

from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis

from app.core.config import REDIS_STATISTICS_URL
from app.kafka.schemas import JobEvent


logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPIC = "jobs"
CONSUMER_GROUP = "insights-group"

INTERVIEW_STATUS = "Собеседование"
REJECTED_STATUS = "Отклонена"

VALID_STATUSES = {
    "Заинтересован",
    "Подана заявка",
    INTERVIEW_STATUS,
    REJECTED_STATUS,
}


def update_status_counter(
    pipe,
    user_id: int,
    old_status: str | None,
    new_status: str | None,
) -> None:
    """
    Обновляет счётчики собеседований и отказов
    в зависимости от старого и нового статуса вакансии.
    """
    key = f"user:{user_id}:job_insights"

    if old_status == INTERVIEW_STATUS:
        pipe.hincrby(key, "interview", -1)

    if old_status == REJECTED_STATUS:
        pipe.hincrby(key, "rejected", -1)

    if new_status == INTERVIEW_STATUS:
        pipe.hincrby(key, "interview", 1)

    if new_status == REJECTED_STATUS:
        pipe.hincrby(key, "rejected", 1)


async def process_event(event: JobEvent, redis: Redis) -> None:
    """
    Обрабатывает события создания, изменения статуса
    и удаления вакансий.

    Счётчики хранят актуальное состояние вакансий,
    а не количество событий за всё время.
    """
    user_id = event.user_id
    job_id = event.data.get("job_id")

    if job_id is None:
        logger.warning(
            "Event has no job_id: %s",
            event.event_type,
        )
        return

    insights_key = f"user:{user_id}:job_insights"
    status_key = f"user:{user_id}:job:{job_id}:status"

    current_status = await redis.get(status_key)

    # Создание вакансии
    if event.event_type == "job.created":

        # Защита от повторной обработки события
        if current_status is not None:
            logger.info(
                "Job already exists in insights: %s",
                job_id,
            )
            return

        new_status = event.data.get("status")

        if new_status not in VALID_STATUSES:
            logger.warning(
                "Invalid status for job.created: %s",
                new_status,
            )
            return

        async with redis.pipeline(transaction=True) as pipe:
            pipe.hincrby(insights_key, "total", 1)

            update_status_counter(
                pipe,
                user_id,
                None,
                new_status,
            )

            pipe.set(status_key, new_status)

            await pipe.execute()

    # Изменение статуса вакансии
    elif event.event_type == "job.status_changed":

        new_status = event.data.get("status")

        if new_status not in VALID_STATUSES:
            logger.warning(
                "Invalid status for job.status_changed: %s",
                new_status,
            )
            return

        if current_status is None:
            logger.warning(
                "Current status not found for job_id=%s",
                job_id,
            )
            return

        # Статус уже обновлён — повторно ничего не делаем
        if current_status == new_status:
            logger.info(
                "Status already updated for job_id=%s",
                job_id,
            )
            return

        async with redis.pipeline(transaction=True) as pipe:
            update_status_counter(
                pipe,
                user_id,
                current_status,
                new_status,
            )

            pipe.set(status_key, new_status)

            await pipe.execute()

    # Удаление вакансии
    elif event.event_type == "job.deleted":

        # Защита от повторного удаления
        if current_status is None:
            logger.info(
                "Job already deleted from insights: %s",
                job_id,
            )
            return

        async with redis.pipeline(transaction=True) as pipe:
            pipe.hincrby(insights_key, "total", -1)

            update_status_counter(
                pipe,
                user_id,
                current_status,
                None,
            )

            pipe.delete(status_key)

            await pipe.execute()

    else:
        logger.info(
            "Event ignored by insights: %s",
            event.event_type,
        )
        return

    logger.info(
        "Insights updated: event_type=%s, user_id=%s, job_id=%s",
        event.event_type,
        user_id,
        job_id,
    )


async def main():
    redis = Redis.from_url(
        REDIS_STATISTICS_URL,
        decode_responses=True,
    )

    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    consumer_started = False

    try:
        await redis.ping()
        logger.info("Insights Consumer: Redis connected")

        await consumer.start()
        consumer_started = True

        logger.info("Insights Consumer started")

        async for message in consumer:
            event = JobEvent.model_validate_json(message.value)

            await process_event(event, redis)

            # Подтверждаем сообщение только после обработки
            await consumer.commit() 

    finally:
        if consumer_started:
            await consumer.stop()

        await redis.aclose()

        logger.info(
            "Insights Consumer stopped and Redis connection closed"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

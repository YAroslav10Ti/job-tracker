
import asyncio
import logging

from aiokafka import AIOKafkaConsumer
from redis.asyncio import Redis

from app.core.config import REDIS_URL
from app.kafka.schemas import JobEvent 
from app.redis.history import add_user_history


logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPIC = "jobs"
CONSUMER_GROUP = "history-group"


# Определяем, какое действие записать в историю
EVENT_ACTIONS = {
    "job.created": "create_job",
    "job.updated": "update_job",
    "job.status_changed": "update_job",
    "job.deleted": "delete_job",
}


async def process_event(
    event: JobEvent,
    redis: Redis,
) -> None:

    action = EVENT_ACTIONS.get(event.event_type)

    if action is None:
        logger.warning(
            "Unknown event type: %s",
            event.event_type,
        )
        return

    await add_user_history(
        redis=redis,
        user_id=event.user_id,
        action=action,
        details=event.data,
    )

    logger.info(
        "History saved: event_type=%s, user_id=%s",
        event.event_type,
        event.user_id,
    )


async def main():

    # Создаём Redis-клиент DB 0
    redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    # Создаём Kafka Consumer
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        enable_auto_commit=False,
        auto_offset_reset="latest",
    )

    try:
        await redis.ping()
        logger.info("History Consumer: Redis connected")

        await consumer.start()
        logger.info("History Consumer started")

        # Постоянно читаем сообщения из Kafka
        async for message in consumer:

            # Преобразуем JSON из Kafka в Pydantic-модель
            event = JobEvent.model_validate_json(
                message.value
            )

            # Обрабатываем событие
            await process_event(event, redis)

            # Подтверждаем обработку сообщения
            await consumer.commit()

    finally:
        await consumer.stop()
        await redis.aclose()

        logger.info("History Consumer stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
    
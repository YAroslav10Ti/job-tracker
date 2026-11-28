import os
# создаем producer для отправки сообщений в Kafka


from aiokafka import AIOKafkaProducer

from app.kafka.schemas import JobEvent 


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

producer: AIOKafkaProducer | None = None


async def start_kafka_producer() -> None:
    global producer

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    )

    await producer.start()


async def stop_kafka_producer() -> None:
    global producer

    if producer is not None:
        await producer.stop()
        producer = None


async def send_event(topic: str, event: JobEvent) -> None:
    if producer is None:
        raise RuntimeError("Kafka Producer is not started")

    message = event.model_dump_json().encode("utf-8")

    await producer.send_and_wait(
        topic,
        message,
    )
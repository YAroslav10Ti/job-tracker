import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from redis.asyncio import Redis
from starlette.routing import Match

from app.core.config import REDIS_URL
from app.kafka.producer import start_kafka_producer, stop_kafka_producer
from app.routers import insights
from app.routers.jobs import router as jobs_router



REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "handler", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "handler"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Redis DB 0
    redis = Redis.from_url(REDIS_URL, decode_responses=True)

    # Redis DB 2
    statistics_redis = Redis.from_url(
        os.getenv("REDIS_STATISTICS_URL", "redis://redis:6379/2"),
        decode_responses=True,
    )

    try:
        await start_kafka_producer()
        print("Kafka producer connected")
    except Exception as exc:
        print(f"Kafka producer failed to start (will work without Kafka): {exc}")

    try:
        await redis.ping()
        app.state.redis = redis
        print("Redis DB 0 connected successfully")

        await statistics_redis.ping()
        app.state.statistics_redis = statistics_redis
        print("Redis DB 2 connected successfully")

        yield

    finally:
        await redis.aclose()
        await statistics_redis.aclose()
        await stop_kafka_producer()
        print("Redis connections closed")


app = FastAPI(
    title="Job Tracker API",
    lifespan=lifespan,
)




def _iter_leaf_routes(routes):
    """Обходит маршруты, включая вложенные роутеры."""
    for route in routes:
        nested = getattr(route, "routes", None)
        if nested is not None and not hasattr(route, "path"):
            yield from _iter_leaf_routes(nested)
        else:
            yield route


def get_route_template(scope) -> str:
    """Возвращает шаблон пути, например /api/jobs/{job_id}, а не конкретный id."""
    try:
        for route in _iter_leaf_routes(app.routes):
            path = getattr(route, "path", None)
            if path is None:
                continue
            match, _ = route.matches(scope)
            if match == Match.FULL:
                return path
    except Exception:
        pass
    return "unmatched"


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)

    handler = get_route_template(request.scope)

    REQUEST_COUNT.labels(request.method, handler, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, handler).observe(time.perf_counter() - start)

    return response


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(jobs_router)
app.include_router(insights.router)


from fastapi.staticfiles import StaticFiles

app.mount(
    "/",
    StaticFiles(directory="/frontend", html=True, check_dir=False),
    name="static",
)
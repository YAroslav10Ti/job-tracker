
from fastapi import Request
from redis.asyncio import Redis 


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_statistics_redis(request: Request) -> Redis:
    return request.app.state.statistics_redis

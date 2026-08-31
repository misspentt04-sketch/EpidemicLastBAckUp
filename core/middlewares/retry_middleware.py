import asyncio
from typing import Any, Callable, Awaitable
from aiogram.client.session.base import BaseRequestMiddleware
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.exceptions import TelegramRetryAfter

class RetryRequestMiddleware(BaseRequestMiddleware):
    def __init__(self, max_retries: int = 2, max_sleep_time: float = 3.0):
        self.max_retries = max_retries
        self.max_sleep_time = max_sleep_time

    async def __call__(
        self,
        make_request: Callable[[TelegramMethod[TelegramType]], Awaitable[TelegramType]],
        bot: Any,
        method: TelegramMethod[TelegramType],
    ) -> TelegramType:
        for attempt in range(self.max_retries):
            try:
                return await make_request(method)
            except TelegramRetryAfter as e:
                # Если задержка небольшая — ждем и пробуем снова
                if e.retry_after <= self.max_sleep_time:
                    await asyncio.sleep(e.retry_after + 0.3)
                else:
                    # Если Telegram просит ждать слишком долго — сбрасываем вызов, 
                    # чтобы не вешать основной поток бота
                    return None
        
        try:
            return await make_request(method)
        except TelegramRetryAfter:
            return None

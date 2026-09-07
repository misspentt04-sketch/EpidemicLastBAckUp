from aiogram import BaseMiddleware
from typing import Awaitable, Callable, Any

class UserRestrictMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event,
        data: dict
    ) -> Any:
        # Пропускаем всё без проверок
        return await handler(event, data)

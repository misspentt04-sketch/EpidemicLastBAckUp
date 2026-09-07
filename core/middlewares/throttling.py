from aiogram import BaseMiddleware
from aiogram.types import Update
from cachetools import TTLCache
from typing import Awaitable, Callable, Dict, Any

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, time_limit: float = 0.1) -> None:
        self.rate_limit = TTLCache(maxsize=10_000, ttl=time_limit)

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get('event_from_user')
        chat = data.get('event_chat')

        if not user:
            return await handler(event, data)

        # Пропускаем команды без троттлинга
        if hasattr(event, 'message') and event.message and event.message.text:
            if event.message.text.startswith('/'):
                return await handler(event, data)

        key = f"{user.id}:{chat.id if chat else 'global'}"
        if key in self.rate_limit:
            return

        self.rate_limit[key] = True
        return await handler(event, data)

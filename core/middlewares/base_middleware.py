from aiogram import BaseMiddleware
from aiogram.types import Update

from typing import Any, Awaitable, Callable


class BaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        return await handler(event, data)

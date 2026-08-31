import asyncio
import time
import logging
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger("ASYNC_OPTIMIZER")

class AsyncOptimizerMiddleware(BaseMiddleware):
    def __init__(self, command_timeout: float = 5.0):
        self.command_timeout = command_timeout

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        try:
            return await asyncio.wait_for(
                handler(event, data), 
                timeout=self.command_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout on command: {event.text}")
            await event.reply("⚠️ Команда выполнялась слишком долго и была сброшена.")
            return None

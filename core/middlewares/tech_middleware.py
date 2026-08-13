import os
from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery

MAINTENANCE_FILE = "/home/ubuntu/epidemic/maintenance.flag"
ALLOWED_USERS = {7972320837, 7958133684}

class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not os.path.exists(MAINTENANCE_FILE):
            return await handler(event, data)

        # Определяем ID пользователя из любого типа апдейта
        user_id = None
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id
            elif event.inline_query and event.inline_query.from_user:
                user_id = event.inline_query.from_user.id
        elif hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id

        # Владельцам разрешено всё
        if user_id in ALLOWED_USERS:
            return await handler(event, data)

        # Полный молчаливый сброс для всех остальных
        return

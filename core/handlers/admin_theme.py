from pyrogram import Client, filters
from pyrogram.types import Message
import json
# Импортируйте вашу функцию/соединение с БД в зависимости от вашего проекта
# Например, если у вас используется SQLAlchemy или асинхронный connection к MySQL/SQLite:
# from core.database import db 

ADMIN_ID = 7972320837

@Client.on_message(filters.command("givetheme") & filters.user(ADMIN_ID))
async def give_admin_theme(client: Client, message: Message):
    # Ожидаемый формат: /givetheme <user_id>
    args = message.command
    if len(args) < 2:
        await message.reply("⚠️ Укажите ID пользователя. Пример: <code>/givetheme 123456789</code>")
        logger_id = getattr(message.from_user, 'id', None)
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ Неверный формат ID пользователя.")
        return

    # Здесь реализуйте логику обновления в БД под ваш проект.
    # Пример для сырого SQL/asyncmy/aiosqlite или вашего ORM:
    # 1. Проверяем пользователя, добавляем 'admin' в купленные темы и ставим active_theme = 'admin'
    
    await message.reply(f"👑 Админ-тема успешно выдана пользователю <code>{target_id}</code>!")

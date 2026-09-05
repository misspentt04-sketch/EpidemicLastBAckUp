import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Bot
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()

@router.message(Command("scan_this_chat"))
async def scan_this_chat(msg: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    if msg.from_user.id not in [7972320837]:
        return

    chat_id = msg.chat.id
    chat = await bot.get_chat(chat_id)
    chat_title = chat.title or chat.full_name or str(chat_id)

    start_msg = await msg.answer(f"🔍 Сканирую чат: {chat_title}...")

    total_users = 0

    try:
        async for member in bot.get_chat_members(chat_id):
            user = member.user
            if not user.is_bot:
                try:
                    await repo_biowar.add_data_user(
                        user.id,
                        user.full_name or "Без имени",
                        user.username
                    )
                    total_users += 1
                except Exception:
                    pass
                await asyncio.sleep(0.05)

        await start_msg.edit_text(f"✅ Зарегистрировано <b>{total_users}</b> пользователей из чата <b>{chat_title}</b>!", parse_mode="HTML")

    except Exception as e:
        await start_msg.edit_text(f"❌ Ошибка: бот не может получить участников. Нужны права администратора.")

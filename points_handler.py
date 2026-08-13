import asyncio
import re
from datetime import datetime
from aiogram import Router, F, types
import pymysql
from core.settings import settings

router = Router()

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user=settings.db.user,
        password=settings.db.password,
        database=settings.db.db,
        autocommit=True
    )

def _is_admin_sync(user_id: int) -> bool:
    # Список Telegram ID главных администраторов бота
    ADMIN_IDS = [7972320837, 8236324289]

    if user_id in ADMIN_IDS:
        return True

    try:
        if hasattr(settings, 'bot'):
            bot_cfg = settings.bot
            if getattr(bot_cfg, 'admin_id', None) == user_id:
                return True

            for attr in ['admin_ids', 'admins', 'owners']:
                ids_list = getattr(bot_cfg, attr, None)
                if ids_list and user_id in ids_list:
                    return True
    except Exception:
        pass

    return False

async def is_admin(user_id: int) -> bool:
    return await asyncio.to_thread(_is_admin_sync, user_id)

def _reset_top_sync():
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute("UPDATE Users SET don_top = 0")
    conn.close()

async def schedule_top_reset():
    while True:
        now = datetime.now()
        if now.weekday() == 6 and now.hour == 22 and now.minute == 0:
            try:
                await asyncio.to_thread(_reset_top_sync)
            except Exception:
                pass
            await asyncio.sleep(3660)
        else:
            await asyncio.sleep(60)

def start_reset_scheduler(bot_instance):
    asyncio.create_task(schedule_top_reset())

def _give_points_sync(target_id: int, amount: int) -> int:
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute("UPDATE Users SET don_top = don_top + %s WHERE id = %s", (amount, target_id))
        affected = c.rowcount
    conn.close()
    return affected

@router.message(F.text.regexp(r"(?i)^(выдать\s+очк[ио])"))
async def give_points_handler(message: types.Message):
    user_id = message.from_user.id
    if not await is_admin(user_id):
        await message.reply(
            "⛔ **Доступ запрещен**\n\n❌ У вас нет прав для использования этой команды.",
            parse_mode="Markdown"
        )
        return

    cleaned_text = re.sub(r"(?i)^выдать\s+очк[ио]\s*", "", message.text.strip())
    params = cleaned_text.split()

    target_id = None
    amount = None

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if len(params) >= 1:
            try:
                amount = int(params[0])
            except ValueError:
                pass

    if not target_id or amount is None:
        if len(params) >= 2:
            try:
                target_id = int(params[0])
                amount = int(params[1])
            except ValueError:
                pass

    if not target_id or amount is None:
        help_text = (
            "📌 **Неверный формат команды!**\n\n"
            "Вы можете использовать один из двух способов:\n\n"
            "1️⃣ **Ответом на сообщение игрока (реплаем):**\n"
            "▫️ `выдать очки <количество>`\n\n"
            "2️⃣ **Указав ID текстом:**\n"
            "▫️ `выдать очки <ID> <количество>`"
        )
        await message.reply(help_text, parse_mode="Markdown")
        return

    try:
        affected = await asyncio.to_thread(_give_points_sync, target_id, amount)
        if affected == 0:
            await message.reply(f"⚠️ **Ошибка:** Пользователь с ID `{target_id}` не найден в базе данных.", parse_mode="Markdown")
            return

        success_text = (
            "✨ **Очки успешно выданы!**\n\n"
            f"👤 **Игрок:** [{target_id}](tg://user?id={target_id})\n"
            f"➕ **Начислено:** `+{amount}` очков"
        )
        await message.reply(success_text, parse_mode="Markdown")
    except Exception:
        await message.reply("❌ **Произошла ошибка при обращении к базе данных.**", parse_mode="Markdown")

def _get_top_sync():
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute("SELECT id, don_top FROM Users WHERE don_top > 0   ORDER BY don_top DESC LIMIT 10")
        rows = c.fetchall()
    conn.close()
    return rows

@router.message(F.text.regexp(r"(?i)^(топ\s+дон|дон\s+топ)"))
async def top_donors_handler(message: types.Message):
    try:
        rows = await asyncio.to_thread(_get_top_sync)
        if not rows:
            await message.reply("📊 **Пока нет данных для топа донатеров.**", parse_mode="Markdown")
            return

        text = "🏆 **Топ донатеров (сброс каждое вс в 22:00):**\n\n"
        for idx, (uid, points) in enumerate(rows, 1):
            text += f"{idx}. [{uid}](tg://user?id={uid}) — **{points}** очков\n"

        await message.reply(text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await message.reply("❌ **Ошибка при загрузке топа из базы данных.**", parse_mode="Markdown")

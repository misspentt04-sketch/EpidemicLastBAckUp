from core.handlers.biowar.rebirth import rebirth_router
from core.handlers.admin_theme_cmd import admin_theme_router
from lab_converter import register_lab_handlers
from core.handlers.tricks.themes import router as themes_router
from core.middlewares.tech_middleware import MaintenanceMiddleware
from maintenance_middleware import MaintenanceMiddleware
import admin_guard
import os
import time
from pyrogram import Client, filters
@Client.on_message(~filters.user(7972320837), group=-100)
async def _admin_only_gate(c, m):
    m.stop_propagation()

from core.middlewares.antispam import AntiSpamMiddleware
from core.handlers.idea import idea_router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.enums.chat_type import ChatType

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.cryptopay import crypto
from redis.asyncio import Redis
from pytz import timezone
from datetime import datetime

from core.middlewares.ac_check import ACMiddleware
from core.middlewares import (
    DBPoolMiddleware, ThrottlingMiddleware, ThrottlingMiddlewareInline,
    UserRestrictMiddleware, ChatMemberUpdateMiddleware
)
from core.filters import IsNotBotFilter, IsNotForwardFilter, IsNotChannelFilter

from core.utils.db_api.settings_pool import db_pool, loop_tasks, scheduler_tasks
from core.utils.commands import set_commands, del_commands
from core.utils.db_api.create_database import db_settings_up
from core.utils.db_api.redis_initialize import redis_initialize

from core.userbot import router as userbot_router
from core.handlers import (
    biowar_router,
    biowar_router2,
    chat_manage_router,
    story_router,
    biowar_global_router,
    suggestions_router
)
from core.handlers.biowar.start_handler import start_router
from points_handler import router as points_router, start_reset_scheduler

from core.settings import settings

import logging
import asyncio

# --- Настройка роутера перезапуска ---
restart_router = Router()
ALLOWED_ADMINS = {7958133684, 7972320837, 1758346431, 7958133684}
RESTART_FILE = "/tmp/epidemic_restart_chat.txt"

@restart_router.message(Command("restart"))
async def restart_cmd(message: types.Message):
    if message.from_user and message.from_user.id in ALLOWED_ADMINS:
        # Сохраняем ID чата
        with open(RESTART_FILE, "w") as f:
            f.write(str(message.chat.id))
        
        os._exit(0)

logging.getLogger("asyncmy").setLevel(logging.ERROR)

async def run_tasks(pool, redis, bot, scheduler):
    asyncio.create_task(loop_tasks(pool, redis, bot))
    asyncio.create_task(scheduler_tasks(pool, redis, bot, scheduler))

async def main():
    logging.basicConfig(level=logging.INFO,
                        format = "%(asctime)s - [%(levelname)s] - %(name)s - "
                        "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s")

    bot = Bot(settings.bots.bot_token, default = DefaultBotProperties(parse_mode=ParseMode.HTML))
    redis_db = Redis(host=settings.redis.ip, port=6379, db=0, decode_responses=True)
    storage = RedisStorage(redis=redis_db)

    dp = Dispatcher()
    from core.middlewares.tech_middleware import MaintenanceMiddleware
    dp.update.outer_middleware.register(MaintenanceMiddleware())
    dp.message.outer_middleware(AntiSpamMiddleware())
    pool = await db_pool.get_pool()
    tz = timezone("Europe/Moscow")
    scheduler = AsyncIOScheduler(timezone=tz)
    lock = asyncio.Lock()

    await bot.delete_webhook(drop_pending_updates = True)

    await del_commands(bot)
    await set_commands(bot)

    await redis_initialize(pool, redis_db)

    # Middlewares
    dp.update.outer_middleware.register(DBPoolMiddleware(pool, redis_db, lock, bot, crypto))
    dp.message.middleware.register(ThrottlingMiddleware(1.5))
    dp.callback_query.middleware.register(ThrottlingMiddlewareInline(0.5))
    dp.chat_member.middleware.register(ChatMemberUpdateMiddleware())
    dp.message.outer_middleware.register(MaintenanceMiddleware())
    dp.callback_query.outer_middleware.register(MaintenanceMiddleware())

    biowar_router.message.middleware.register(UserRestrictMiddleware(redis_db))
    biowar_router2.message.middleware.register(UserRestrictMiddleware(redis_db))

    dp.update.outer_middleware(MaintenanceMiddleware())
    
    # Регистрируем catch_infection ПЕРВЫМ
    from aiogram import F as AiogramF
    from aiogram.types import Message as AiogramMessage
    
    @dp.message(AiogramF.text.contains("подверг заражению"))
    async def catch_infection_global(msg: AiogramMessage):
        import sqlite3 as sql
        from datetime import datetime as dt, timedelta as td
        from pathlib import Path
        
        try:
            text = msg.text
            if not text:
                return
            
            attacker_id_match = re.search(r'user_id=(\d+)', text)
            if not attacker_id_match:
                return
            
            attacker_id = int(attacker_id_match.group(1))
            
            victim_match = re.search(r'патогеном\s+(.+)', text)
            if not victim_match:
                return
            
            victim_text = victim_match.group(1)
            victim_id_match = re.search(r'user_id=(\d+)', victim_text)
            victim_id = int(victim_id_match.group(1)) if victim_id_match else None
            
            days_match = re.search(r'🤒\s+Заражение\s+на\s+(\d+)\s+дней', text)
            days = int(days_match.group(1)) if days_match else 0
            
            bio_match = re.search(r'☣️\s+\+([\d,]+)\s+био-опыта', text)
            bio_earn = int(bio_match.group(1).replace(',', '')) if bio_match else 0
            
            from core.userbot.chk_handler import get_or_create_client, get_ordered_sessions
            
            attacker_username = None
            for username in get_ordered_sessions():
                client = await get_or_create_client(username)
                if client:
                    me = await client.get_me()
                    if me.id == attacker_id:
                        attacker_username = username
                        break
            
            if not attacker_username:
                return
            
            db_path = Path("data/victims.db")
            now = dt.now()
            expire_date = now + td(days=days) if days > 0 else now
            
            conn = sql.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO victims (attacker_username, attacker_id, victim_id, victim_username, bio_earn, infected_date, expire_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (attacker_username, attacker_id, victim_id, str(victim_id), bio_earn, now.strftime('%Y-%m-%d %H:%M:%S'), expire_date.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            print(f"✅ ЗАПИСАНА ЖЕРТВА: @{attacker_username} -> {victim_id}, +{bio_earn}")
            
        except Exception as e:
            print(f"❌ Ошибка записи жертвы: {e}")
    
    dp.include_routers(
        rebirth_router,
        userbot_router,
        admin_theme_router, 
        themes_router,
        restart_router,
        start_router,
        idea_router,
        biowar_router,
        biowar_router2,
        biowar_global_router,
        story_router,
        chat_manage_router,
        suggestions_router,
        points_router
    )

    start_reset_scheduler(dp)

    await run_tasks(pool, redis_db, bot, scheduler)

    print("Started successfully!")
    
    # Запускаем слушатель заражений
    from core.userbot.chk_handler import start_victim_listener
    await start_victim_listener()
    


    # Проверка: если был /restart, отправляем красивый отчёт
    if os.path.exists(RESTART_FILE):
        try:
            with open(RESTART_FILE, "r") as f:
                chat_id = int(f.read().strip())
            os.remove(RESTART_FILE)

            # Замер пинга до серверов Telegram
            start_ping = time.perf_counter()
            me = await bot.get_me()
            ping_ms = round((time.perf_counter() - start_ping) * 1000, 2)

            # Время запуска
            start_time = datetime.now(tz).strftime("%H:%M:%S (%d.%m.%Y)")

            text = (
                "🛡 <b>Вышел на службу!</b>\n\n"
                f"⏰ <b>Время старта:</b> <code>{start_time}</code>\n"
                f"⚡ <b>Пинг:</b> <code>{ping_ms} ms</code>"
            )
            await bot.send_message(chat_id, text)
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления о запуске: {e}")

    scheduler.start()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

# Регистрация модуля конвертера лаборатории
# register_lab_handlers(app)

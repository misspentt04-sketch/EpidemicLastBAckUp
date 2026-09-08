import logging
import asyncio
from aiogram import Bot
from asyncmy.pool import Pool
from redis.asyncio import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ===== АВТОСТАРТ БОССА (каждые 4 часа, шанс 25%) =====
    import random
    from core.handlers.biowar.boss import spawn_boss

    # Проверяем, активен ли босс
    is_active = await redis.get("boss:active")
    if is_active:
        logging.info("[BOSS AUTO] Босс уже активен")
        return

    # Шанс 25%
    if random.random() > 0.25:
        logging.info("[BOSS AUTO] Шанс не выпал, босс не создан")
        return

    # Создаём босса
    max_hp = await spawn_boss(pool, redis)

    # Уведомление в канал
    try:
        await bot.send_message(
            -1004335676077,
            f"🧟 <b>Босс появился!</b>\n\n"
            f"❤️ HP: <b>{max_hp:,}</b>\n"
            f"⏳ Время: 1 час\n"
            f"⚔️ Атакуйте через <code>/boss</code>!\n"
            f"🏆 Топ-3 получат награды!",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.info(f"[BOSS AUTO CHANNEL ERROR] {e}")

    logging.info(f"[BOSS AUTO] Босс создан! HP: {max_hp}")



async def scheduler_tasks(pool: Pool, redis: Redis, bot: Bot, scheduler: AsyncIOScheduler):
    logging.info("[SCHEDULER] === ФУНКЦИЯ ЗАПУЩЕНА ===")
    import asyncio
    await asyncio.sleep(5)
    logging.info("[SCHEDULER] scheduler_tasks вызвана!")

    )


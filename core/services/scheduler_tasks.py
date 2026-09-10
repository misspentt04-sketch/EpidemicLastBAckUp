import logging
import random
from redis.asyncio import Redis
from datetime import datetime, timedelta
from aiogram import Bot
from asyncmy.pool import Pool
from core.settings import moscow_tz

async def gave_victims_food(pool: Pool):
    """Выдача корма жертвам в 12:00 и 00:00"""
    print("[TICK] gave_victims_food вызвана!")
    sql_update_lab = (
        "UPDATE Lab l JOIN ("
        " SELECT v.victims_owner_id, SUM(v.victim_bio_resource_earn) * (1 + COALESCE(l2.rebirth_level, 0) * 0.10) AS bio_resource"
        " FROM Victims v"
        " LEFT JOIN Lab l2 ON l2.lab_id = v.victims_owner_id"
        " GROUP BY v.victims_owner_id"
        ") v ON l.lab_id = v.victims_owner_id "
        "SET l.bio_resource = l.bio_resource + v.bio_resource;"
    )
    sql_del_victims = "DELETE FROM Victims WHERE victim_expire < %s;"
    sql_update_service = "UPDATE Service SET time_give_food=%s;"

    try:
        now = datetime.now(moscow_tz)
        if now.hour < 12:
            next_dt = now.replace(hour=12, minute=0, second=0, microsecond=0)
        else:
            next_dt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql_update_lab)
                now_ts = int(datetime.now().timestamp())
                await cur.execute(sql_del_victims, (now_ts,))
                await cur.execute(sql_update_service, (int(next_dt.timestamp()),))
    except Exception as e:
        print(f"Ошибка в gave_victims_food: {e}")

async def send_weekly_top_report(bot: Bot):
    """Еженедельный отчёт по топам"""
    try:
        # Здесь будет логика отправки отчёта
        print("[SCHEDULER] Еженедельный отчёт отправлен")
    except Exception as e:
        print(f"[SCHEDULER] Ошибка weekly: {e}")

async def send_monthly_top_report(bot: Bot):
    """Ежемесячный отчёт по топам"""
    try:
        # Здесь будет логика отправки отчёта
        print("[SCHEDULER] Ежемесячный отчёт отправлен")
    except Exception as e:
        print(f"[SCHEDULER] Ошибка monthly: {e}")

# ===== АВТОЗАПУСК БОССА В 20:00 МСК =====
async def auto_start_boss(pool: Pool, redis: Redis, bot: Bot):
    """Автоматический запуск босса каждый день в 20:00"""
    try:
        # Проверяем, активен ли босс
        is_active = await redis.get("boss:active")
        if is_active:
            print("[BOSS] Босс уже активен, пропускаем запуск")
            return
        
        # Импортируем функцию spawn_boss из boss.py
        from core.handlers.biowar.boss import spawn_boss
        
        # Запускаем босса
        max_hp = await spawn_boss(pool, redis)
        
        # Уведомление в канал
        await bot.send_message(
            -1004335676077,
            f"🧟 <b>Босс создан!</b>\n\n"
            f"❤️ HP: <b>{max_hp:,}</b>\n"
            f"⏳ Время: 1 час\n"
            f"⚔️ Атакуйте через <code>/boss</code>!\n"
            f"🏆 Топ-3 получат награды!",
            parse_mode="HTML"
        )
        
        print(f"[BOSS] Босс автоматически создан в 20:00! HP: {max_hp:,}")
        
    except Exception as e:
        print(f"[BOSS AUTO START ERROR] {e}")

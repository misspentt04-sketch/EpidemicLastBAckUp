import time
from aiogram import Router, F
from aiogram.types import Message
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor
from redis.asyncio import Redis

router = Router()

# ===== НАСТРОЙКИ =====
REWARD_RESOURCE = 10_000
REWARD_EXP = 500
COOLDOWN = 60 * 60  # 1 час

# ===== ТЕКСТЫ КОМАНД (любой регистр) =====
COMMANDS = [
    "дед пидорас",
    "дед хуесос",
]


@router.message(F.text.regexp(r'(?i)^\S+\s+(хуесос|пидорас)$'))
async def cmd_ded(msg: Message, pool: Pool, redis: Redis):
    user_id = msg.from_user.id

    # ===== КД 10 МИНУТ =====
    cooldown_key = f"ded_cooldown:{user_id}"
    last = await redis.get(cooldown_key)
    if last:
        remaining = COOLDOWN - (int(time.time()) - int(last))
        if remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60
            if minutes > 0:
                time_str = f"{minutes}м {seconds}с"
            else:
                time_str = f"{seconds}с"
            return await msg.reply(
                f"⏳ <b>КД!</b>\n\nПодожди ещё <b>{time_str}</b>",
                parse_mode="HTML"
            )

    # ===== ПРОВЕРЯЕМ ЛАБУ =====
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT lab_id FROM Lab WHERE lab_id = %s",
                (user_id,)
            )
            lab = await cur.fetchone()

    if not lab:
        return await msg.reply("❌ У вас нет лаборатории!")

    # ===== НАЧИСЛЯЕМ =====
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                UPDATE Lab
                SET bio_resource = bio_resource + %s,
                    bio_experience = bio_experience + %s
                WHERE lab_id = %s
            """, (REWARD_RESOURCE, REWARD_EXP, user_id))

    # ===== СТАВИМ КД =====
    await redis.set(cooldown_key, int(time.time()), ex=COOLDOWN)

    await msg.reply(
        f"🎁 <b>Награда получена!</b>\n\n"
        f"💰 +{REWARD_RESOURCE:,} 🧬\n"
        f"⭐ +{REWARD_EXP:,} XP\n\n"
        f"⏳ Следующая награда через 1 час",
        parse_mode="HTML"
    )

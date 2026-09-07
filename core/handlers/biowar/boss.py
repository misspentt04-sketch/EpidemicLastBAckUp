import time
import random
from datetime import datetime, timedelta
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.pool import Pool
from redis.asyncio import Redis

router = Router()

BOSS_STICKER = "CAACAgIAAxkBAAER3bRqnrlPKu8usp1KpsKlwSmDa0twSQACNwMAAu7EoQpGEtmG9sGJBz0E"
LOG_CHAT = -1003688648228

REWARDS = {
    1: {"place": "🥇 1 место", "epicoins": 1000, "cases": 3, "exp": 10000},
    2: {"place": "🥈 2 место", "epicoins": 500, "cases": 1, "exp": 3000},
    3: {"place": "🥉 3 место", "epicoins": 300, "cases": 0, "exp": 1000},
}

ATTACK_COOLDOWN = 60

# ===== ФУНКЦИИ =====
async def get_hp_bar(hp: int, max_hp: int, length: int = 20):
    if max_hp <= 0:
        return "💀 Мёртв"
    percent = hp / max_hp
    filled = int(percent * length)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    return f"{bar} {percent:.1%}"

async def get_attackers_count(pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(DISTINCT user_id) FROM BossAttacks WHERE boss_id = (SELECT id FROM Boss ORDER BY id DESC LIMIT 1)")
            row = await cur.fetchone()
            return row[0] if row else 0

async def get_all_attackers(pool: Pool, boss_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id, SUM(damage) as total_damage
                FROM BossAttacks
                WHERE boss_id = %s
                GROUP BY user_id
                ORDER BY total_damage DESC
            """, (boss_id,))
            return await cur.fetchall()

async def get_top_attackers(pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id, SUM(damage) as total_damage
                FROM BossAttacks
                WHERE boss_id = (SELECT id FROM Boss ORDER BY id DESC LIMIT 1)
                GROUP BY user_id
                ORDER BY total_damage DESC
                LIMIT 10
            """)
            return await cur.fetchall()

async def get_top_damage(pool: Pool):
    rows = await get_top_attackers(pool)
    if not rows:
        return "Пока никто не атаковал 💤"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    lines = []
    for i, row in enumerate(rows):
        if isinstance(row, dict):
            user_id = row.get('user_id')
            damage = row.get('total_damage') or 0
        else:
            user_id = row[0]
            damage = row[1] if len(row) > 1 else 0
        user_name = str(user_id)
        try:
            async with pool.acquire() as conn2:
                async with conn2.cursor() as cur2:
                    await cur2.execute("SELECT full_name FROM Users WHERE id = %s", (user_id,))
                    user_row = await cur2.fetchone()
                    if user_row:
                        if isinstance(user_row, dict):
                            user_name = user_row.get('full_name') or str(user_id)
                        else:
                            user_name = user_row[0] if user_row[0] else str(user_id)
        except:
            pass
        medal = medals[i] if i < len(medals) else f"{i+1}."
        lines.append(f"{medal} <b>{user_name}</b> (<code>{user_id}</code>) — <b>{damage:,}</b> урона")
    return "\n".join(lines)

async def get_top_winners(pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id, wins, total_damage
                FROM BossWinners
                ORDER BY wins DESC
                LIMIT 5
            """)
            rows = await cur.fetchall()
    if not rows:
        return "Пока нет победителей 💤"
    medals = ["👑", "🥈", "🥉", "4️⃣", "5️⃣"]
    lines = []
    for i, row in enumerate(rows):
        if isinstance(row, dict):
            user_id = row.get('user_id')
            wins = row.get('wins') or 0
            total_damage = row.get('total_damage') or 0
        else:
            user_id = row[0]
            wins = row[1] if len(row) > 1 else 0
            total_damage = row[2] if len(row) > 2 else 0
        medal = medals[i] if i < 5 else f"{i+1}."
        lines.append(f"{medal} <code>{user_id}</code> — <b>{wins}</b> побед, урон: <b>{total_damage:,}</b>")
    return "\n".join(lines)

def format_time(seconds: int):
    if seconds <= 0:
        return "Завершён"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}ч {minutes}м"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    return f"{secs}с"

async def spawn_boss(pool: Pool, redis: Redis):
    await redis.set("boss:active", "1")
    await redis.set("boss:id", 1)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM Lab")
            count = await cur.fetchone()
            players = count[0] if count else 100
    max_hp = players * 20
    await redis.set("boss:hp", max_hp)
    await redis.set("boss:max_hp", max_hp)
    end_time = int(time.time()) + 3600
    await redis.set("boss:end_time", end_time)
    return max_hp

async def send_boss_menu(target, redis: Redis, pool: Pool, is_callback: bool = False):
    is_active = await redis.get("boss:active")
    hp = int(await redis.get("boss:hp") or 0)
    max_hp = int(await redis.get("boss:max_hp") or 1)
    end_time = await redis.get("boss:end_time")

    if is_active and hp > 0:
        status = "🟢 ЖИВ"
        hp_bar = await get_hp_bar(hp, max_hp)
        remaining = int(end_time) - int(time.time()) if end_time else 0
        remaining_str = format_time(remaining) if remaining > 0 else "⏳ Завершается..."
    else:
        status = "🔴 МЁРТВ / НЕ АКТИВЕН"
        hp_bar = "💀 Повержен"
        remaining_str = "⏳ Запустите босса командой /start_boss (админ)"

    attackers_count = await get_attackers_count(pool)
    top_damage = await get_top_damage(pool)

    text = (
        f"🧟 <b>Эпидемический Босс</b>\n\n"
        f"📊 <b>Статус:</b> {status}\n"
        f"❤️ <b>HP:</b> {hp_bar}\n"
        f"📈 <b>Осталось HP:</b> <code>{hp:,}</code> / <code>{max_hp:,}</code>\n"
        f"⏳ <b>До конца:</b> {remaining_str}\n"
        f"👥 <b>Атакующих:</b> <code>{attackers_count}</code>\n\n"
        f"🔥 <b>Топ урона (этот босс):</b>\n{top_damage}\n\n"
        f"⚔️ Нажмите кнопку ниже, чтобы атаковать босса!\n⏱️ КД между атаками: <b>1 минута</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Атаковать", callback_data="boss_attack"), InlineKeyboardButton(text="🏆 Топ урона", callback_data="boss_top_damage")],
        [InlineKeyboardButton(text="👑 Топ победителей", callback_data="boss_top_winners"), InlineKeyboardButton(text="🔄 Обновить", callback_data="boss_refresh")]
    ])

    if is_callback:
        await target.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await target.reply(text, reply_markup=kb, parse_mode="HTML")

# ===== КОМАНДА /BOSS =====
@router.message(F.text.lower() == "/boss")
async def cmd_boss(msg: Message, **kwargs):
    redis = kwargs.get("redis")
    pool = kwargs.get("pool")
    if not redis or not pool:
        await msg.reply("❌ Ошибка: сервисы не инициализированы!")
        return
    try:
        await msg.reply_sticker(BOSS_STICKER)
    except:
        await msg.reply("⚠️ Стикер не найден")
    await send_boss_menu(msg, redis, pool, is_callback=False)

# ===== АДМИН: ЗАПУСТИТЬ БОССА =====
@router.message(F.text.lower() == "/start_boss")
async def start_boss(msg: Message, **kwargs):
    user_id = msg.from_user.id
    if user_id != 7972320837:
        await msg.reply("❌ У вас нет прав!")
        return
    redis = kwargs.get("redis")
    pool = kwargs.get("pool")
    if not redis or not pool:
        await msg.reply("❌ Ошибка сервисов!")
        return
    is_active = await redis.get("boss:active")
    if is_active:
        hp = int(await redis.get("boss:hp") or 0)
        if hp > 0:
            await msg.reply("❌ Босс уже активен!")
            return
    max_hp = await spawn_boss(pool, redis)
    await msg.reply(
        f"🧟 <b>Босс создан!</b>\n\n❤️ HP: <b>{max_hp:,}</b>\n⏳ Время: 1 час\n⏱️ КД: 1 минута\n\n"
        f"🏆 <b>Награды:</b>\n🥇 1 место — 10 000 опыта + 3 кейса + 1 000 🪙\n"
        f"🥈 2 место — 3 000 опыта + 1 кейс + 500 🪙\n🥉 3 место — 1 000 опыта + 300 🪙\n\n"
        f"⚔️ <b>Урон:</b> БЕЗОПАСНОСТЬ (×3) + ЗАРАЗНОСТЬ (×1) + ЛЕТАЛЬНОСТЬ (×2)\n🎲 Рандом: ±50%\n\n"
        f"Атакуйте через <code>/boss</code>!",
        parse_mode="HTML"
    )

# ===== АТАКА БОССА =====
@router.callback_query(F.data == "boss_attack")
async def boss_attack(call: CallbackQuery, **kwargs):
    user_id = call.from_user.id
    redis = kwargs.get("redis")
    pool = kwargs.get("pool")
    repo_biowar = kwargs.get("repo_biowar")
    
    if not redis or not pool or not repo_biowar:
        await call.answer("❌ Ошибка сервисов!", show_alert=True)
        return
    
    cooldown_key = f"boss_cooldown:{user_id}"
    last_attack = await redis.get(cooldown_key)
    if last_attack:
        remaining = ATTACK_COOLDOWN - (int(time.time()) - int(last_attack))
        if remaining > 0:
            await call.answer(f"⏳ Подожди {remaining} сек!", show_alert=True)
            return
    
    is_active = await redis.get("boss:active")
    if not is_active:
        await call.answer("❌ Босс не активен!", show_alert=True)
        return
    
    hp = int(await redis.get("boss:hp") or 0)
    if hp <= 0:
        await call.answer("❌ Босс мёртв!", show_alert=True)
        return
    
    lab = await repo_biowar.get_info_user_lab(user_id)
    if not lab:
        await call.answer("❌ Нет лаборатории!", show_alert=True)
        return
    
    security = lab.get("security_service", 0)
    infect = lab.get("infect", 0)
    lethality = lab.get("lethality", 0)

    base_damage = security * 3 + infect * 1 + lethality * 2
    base_damage = max(5, base_damage)
    damage = int(base_damage * random.uniform(0.5, 1.5))
    damage = max(1, damage)

    new_hp = max(0, hp - damage)
    await redis.set("boss:hp", new_hp)
    await redis.set(cooldown_key, str(int(time.time())), ex=ATTACK_COOLDOWN)
    
    boss_id = int(await redis.get("boss:id") or 0)
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO BossAttacks (boss_id, user_id, damage) VALUES (%s, %s, %s)", (boss_id, user_id, damage))
    except Exception as e:
        print(f"[BOSS ATTACK ERROR] {e}")
    
    immunity = lab.get("immunity", 0)
    back_damage = min(int(damage * max(0.01, 0.08 - (immunity * 0.001))), 500)
    if back_damage > 0:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s", (back_damage, user_id))
    
    try:
        await call.answer(f"⚔️ Нанесено {damage:,} урона!", show_alert=True)
    except:
        pass

    if new_hp <= 0:
        await redis.delete("boss:active", "boss:hp", "boss:max_hp", "boss:id")
        await call.message.edit_text(
            f"🎉 <b>БОСС ПОВЕРЖЕН!</b>\n\n"
            f"⚔️ Вы нанесли <b>{damage:,}</b> урона!\n"
            f"💢 Ответ: <b>-{back_damage:,}</b> ресурсов",
            parse_mode="HTML"
        )
        await give_rewards(call, pool, redis, boss_id)
        return

    await send_boss_menu(call.message, redis, pool, is_callback=True)

# ===== ВЫДАЧА НАГРАД =====
async def give_rewards(call: CallbackQuery, pool: Pool, redis: Redis, boss_id: int):
    all_attackers = await get_all_attackers(pool, boss_id)
    if not all_attackers:
        return
    top_3 = all_attackers[:3]
    
    for i, (user_id, damage) in enumerate(top_3, start=1):
        reward = REWARDS.get(i)
        if not reward:
            continue
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE Lab SET epicoins = epicoins + %s, case1 = case1 + %s, bio_experience = bio_experience + %s WHERE lab_id = %s
                """, (reward["epicoins"], reward["cases"], reward["exp"], user_id))
        try:
            await call.bot.send_message(
                user_id,
                f"🏆 <b>Вы заняли {i} место!</b>\n\n⚔️ Урон: {damage:,}\n"
                f"🎁 +{reward['exp']:,} опыта\n📦 +{reward['cases']} кейсов\n🪙 +{reward['epicoins']:,} эпикоинов",
                parse_mode="HTML"
            )
        except:
            pass

    for user_id, damage in top_3:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO BossWinners (user_id, wins, total_damage)
                    VALUES (%s, 1, %s)
                    ON DUPLICATE KEY UPDATE wins = wins + 1, total_damage = total_damage + %s
                """, (user_id, damage, damage))

    log_text = f"🧟 <b>Босс повержен!</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (user_id, damage) in enumerate(top_3, start=1):
        log_text += f"{medals[i-1]} <code>{user_id}</code> — <b>{damage:,}</b> урона\n"
    log_text += f"\n📊 Всего атакующих: {len(all_attackers)}"
    
    try:
        await call.bot.send_message(LOG_CHAT, log_text, parse_mode="HTML")
    except:
        pass

# ===== ОСТАЛЬНЫЕ CALLBACK =====
@router.callback_query(F.data == "boss_refresh")
async def boss_refresh(call: CallbackQuery, **kwargs):
    await call.answer("🔄 Обновляю...")
    redis = kwargs.get("redis")
    pool = kwargs.get("pool")
    if redis and pool:
        await send_boss_menu(call.message, redis, pool, is_callback=True)

@router.callback_query(F.data == "boss_top_damage")
async def boss_top_damage(call: CallbackQuery, **kwargs):
    pool = kwargs.get("pool")
    if not pool:
        await call.answer("❌ Ошибка!", show_alert=True)
        return
    top = await get_top_damage(pool)
    await call.message.answer(f"🏆 <b>Топ урона</b>\n\n{top}", parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "boss_top_winners")
async def boss_top_winners(call: CallbackQuery, **kwargs):
    pool = kwargs.get("pool")
    if not pool:
        await call.answer("❌ Ошибка!", show_alert=True)
        return
    top = await get_top_winners(pool)
    await call.message.answer(f"👑 <b>Топ победителей</b>\n\n{top}", parse_mode="HTML")
    await call.answer()

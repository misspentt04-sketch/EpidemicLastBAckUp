"""
Акции в кейсах:
  - 3 лота в день (навык или кейс).
  - Скидка 1–25%, валюта 🧬 или 🪙.
  - Сброс в 00:00 МСК.
  - Хранение в Redis: discount:{user_id}
"""
import json
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor
from redis.asyncio import Redis

from core.func import lvl_up_calc

router = Router()

# ===== НАСТРОЙКИ =====
MOSCOW_TZ = timezone(timedelta(hours=3))
RATE_EPICOINS_TO_RES = 10000  # 1 🪙 = 10 000 🧬

CASE_PRICES = {
    "case1": {"resources": 5_000_000, "epicoins": 500, "name": "📦 Обычный кейс"},
    "case2": {"resources": 12_000_000, "epicoins": 1500, "name": "💎 Донат-кейс"},
}

SKILLS_MAP = {
    "infect": "зз",
    "immunity": "иммун",
    "science": "разраб",
    "lethality": "летал",
    "security_service": "сб",
}

SKILLS_DB = {
    "infect": "infect",
    "immunity": "immunity",
    "science": "science",
    "lethality": "lethality",
    "security_service": "security_service",
}


# ===== ВРЕМЯ ДО 00:00 МСК =====
def seconds_until_midnight_msk() -> int:
    """Сколько секунд до следующего 00:00 МСК"""
    now_msk = datetime.now(MOSCOW_TZ)
    tomorrow = (now_msk + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int((tomorrow - now_msk).total_seconds())


def format_time_left(seconds: int) -> str:
    """Форматирует секунды в 'Xч Yм'"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        return f"{h}ч {m}м"
    return f"{m}м"


# ===== ГЕНЕРАЦИЯ АКЦИЙ =====
def generate_act(act_id: int, lab_info: dict = None) -> dict:
    """Генерирует один лот.
    lab_info — словарь с уровнями навыков игрока (может быть None).
    """
    # Доступные навыки — исключаем те, что на максимуме
    available_skills = list(SKILLS_MAP.keys())

    # Разработка НИКОГДА не в акциях
    if "science" in available_skills:
        available_skills.remove("science")

    if lab_info:
        # Разработка >= 55 → исключаем science
        if lab_info.get("science", 0) >= 55 and "science" in available_skills:
            available_skills.remove("science")

        # Патогены на максимуме → исключаем pathogens
        if lab_info.get("pathogens", 0) and lab_info.get("ready_pathogens", 0) >= lab_info.get("pathogens", 0):
            if "pathogens" in available_skills:
                available_skills.remove("pathogens")

    # Если все навыки исключены — только кейсы
    if not available_skills:
        # Только кейс
        case_type = "case1" if random.random() < 0.7 else "case2"
        act = {
            "id": act_id,
            "type": "case",
            "case_type": case_type,
            "discount": random.randint(1, 25) / 100,
            "purchased": False,
        }
    elif random.random() < 0.8:
        # Навык
        skill = random.choice(available_skills)
        levels = random.randint(1, 5)
        act = {
            "id": act_id,
            "type": "skill",
            "skill": skill,
            "levels": levels,
            "discount": random.randint(1, 25) / 100,
            "purchased": False,
        }
    else:
        # Кейс
        case_type = "case1" if random.random() < 0.7 else "case2"
        act = {
            "id": act_id,
            "type": "case",
            "case_type": case_type,
            "discount": random.randint(1, 25) / 100,
            "purchased": False,
        }

    # Валюта — рандом
    act["currency"] = random.choice(["resources", "epicoins"])
    return act


def generate_acts(lab_info: dict = None) -> list:
    """3 лота. lab_info — уровни навыков игрока (для исключений)."""
    return [generate_act(i + 1, lab_info) for i in range(3)]


# ===== REDIS =====
async def get_acts(redis: Redis, user_id: int, lab_info: dict = None) -> Optional[dict]:
    """Читает акции из Redis. Если нет/просрочены — генерирует.
    lab_info — уровни навыков (для исключения science >= 55).
    """
    key = f"discount:{user_id}"
    data = await redis.get(key)

    if data:
        try:
            acts_data = json.loads(data)
            return acts_data
        except Exception:
            pass

    # Генерируем новые
    new_data = {
        "date": datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d"),
        "acts": generate_acts(lab_info),
    }
    ttl = seconds_until_midnight_msk()
    await redis.set(key, json.dumps(new_data), ex=ttl)
    return new_data


async def save_acts(redis: Redis, user_id: int, acts_data: dict):
    """Сохраняет акции (TTL сохраняется)"""
    key = f"discount:{user_id}"
    # Оставляем исходный TTL
    ttl = await redis.ttl(key)
    if ttl <= 0:
        ttl = seconds_until_midnight_msk()
    await redis.set(key, json.dumps(acts_data), ex=ttl)


# ===== РАСЧЁТ ЦЕНЫ =====
async def get_act_price(pool: Pool, user_id: int, act: dict) -> tuple[int, int]:
    """Возвращает (base_price, final_price) для акции"""
    if act["type"] == "skill":
        # Получаем текущий уровень навыка
        skill_db = act["skill"]
        async with pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    f"SELECT {skill_db} FROM Lab WHERE lab_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()

        if not row:
            return 0, 0

        current_lvl = row[skill_db]
        from_lvl = current_lvl
        to_lvl = current_lvl + act["levels"]

        # Базовая цена (в 🧬)
        base_res = lvl_up_calc(skill_db, from_lvl, to_lvl)

        # Цена со скидкой (в 🧬)
        final_res = int(base_res * (1 - act["discount"]))

        if act["currency"] == "epicoins":
            # Пересчёт в 🪙 — СНАЧАЛА скидка, ПОТОМ деление на курс
            base_ep = max(1, round(base_res / RATE_EPICOINS_TO_RES))
            final_ep = max(1, round(final_res / RATE_EPICOINS_TO_RES))
            return base_ep, final_ep
        else:
            return base_res, final_res

    else:  # case
        case_info = CASE_PRICES[act["case_type"]]
        if act["currency"] == "epicoins":
            base = case_info["epicoins"]
        else:
            base = case_info["resources"]
        final = int(base * (1 - act["discount"]))
        return base, final


# ===== ФОРМИРОВАНИЕ ТЕКСТА =====
async def build_acts_text(pool: Pool, redis: Redis, user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Строит текст меню акций и клавиатуру"""
    acts_data = await get_acts(redis, user_id)
    acts = acts_data["acts"]

    sec_left = seconds_until_midnight_msk()

    lines = [
        "🔥 <b>АКЦИИ</b>",
        f"⏳ Сброс в <b>00:00 МСК</b> (через {format_time_left(sec_left)})",
        "",
    ]

    emojis = ["1️⃣", "2️⃣", "3️⃣"]
    kb_rows = []

    for i, act in enumerate(acts):
        emoji = emojis[i]

        if act["type"] == "skill":
            skill_name = SKILLS_MAP[act["skill"]]
            title = f"➕ +{act['levels']} {skill_name}"
        else:
            title = CASE_PRICES[act["case_type"]]["name"]

        if act["purchased"]:
            lines.append(f"{emoji} {title}")
            lines.append(f"    ✅ <b>Куплено</b>")
            lines.append("")
        else:
            base_price, final_price = await get_act_price(pool, user_id, act)
            currency = "🧬" if act["currency"] == "resources" else "🪙"
            discount_pct = int(act["discount"] * 100)

            lines.append(f"{emoji} {title}")
            lines.append(
                f"    💰 <s>{base_price:,} {currency}</s> → "
                f"<b>{final_price:,} {currency}</b> (скидка {discount_pct}%)"
            )
            lines.append("")

        # Кнопка
        if act["purchased"]:
            btn_text = f"❌ Куплен лот {i+1}"
        else:
            btn_text = f"✅ Купить лот {i+1}"
        kb_rows.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"act:buy:{i+1}")
        ])

    kb_rows.append([
        InlineKeyboardButton(
            text="🔄 Обновить акции (300🪙 / 3M🧬)",
            callback_data="acts_reroll"
        )
    ])
    kb_rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="shop_back")])

    text = "\n".join(lines)
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    return text, kb


# ===== ХЕНДЛЕР: ОТКРЫТЬ МЕНЮ АКЦИЙ =====
# ===== ИСПОЛЬЗОВАНИЕ АКЦИЙ В ПРОКАЧКЕ =====
async def check_skill_act(redis: Redis, user_id: int, skill: str, from_lvl: int, to_lvl: int) -> dict | None:
    """
    Ищет активную акцию на навык.
    Возвращает act dict или None.
    """
    acts_data = await get_acts(redis, user_id)
    for act in acts_data["acts"]:
        if act["type"] != "skill":
            continue
        if act["purchased"]:
            continue
        if act["skill"] != skill:
            continue
        # Проверяем, что диапазон уровней совпадает
        # (акция +5, игрок покупает +5 — совпадает)
        return act
    return None


async def mark_act_purchased(redis: Redis, user_id: int, act_id: int):
    """Помечает акцию как купленную"""
    acts_data = await get_acts(redis, user_id)
    for act in acts_data["acts"]:
        if act["id"] == act_id:
            act["purchased"] = True
            break
    await save_acts(redis, user_id, acts_data)


# ===== СБРОС / ОБНОВЛЕНИЕ АКЦИЙ =====
REROLL_PRICE_EPICOINS = 300
REROLL_PRICE_RESOURCES = 3_000_000


async def reset_acts(redis: Redis, user_id: int):
    """Полностью пересоздаёт 3 лота, TTL сохраняется до 00:00 МСК"""
    key = f"discount:{user_id}"
    ttl = await redis.ttl(key)
    if ttl <= 0:
        ttl = seconds_until_midnight_msk()

    new_data = {
        "date": datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d"),
        "acts": generate_acts(),
    }
    await redis.set(key, json.dumps(new_data), ex=ttl)
    return new_data


@router.callback_query(F.data == "acts_reroll")
async def cb_acts_reroll(call: CallbackQuery, pool: Pool, redis: Redis):
    user_id = call.from_user.id

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT bio_resource, epicoins FROM Lab WHERE lab_id = %s",
                (user_id,)
            )
            lab = await cur.fetchone()

    if not lab:
        return await call.answer("❌ Нет лаборатории!", show_alert=True)

    use_epicoins = lab["epicoins"] >= REROLL_PRICE_EPICOINS
    use_resources = (not use_epicoins) and (lab["bio_resource"] >= REROLL_PRICE_RESOURCES)

    if not use_epicoins and not use_resources:
        return await call.answer(
            f"❌ Недостаточно средств!\n"
            f"💰 Нужно: {REROLL_PRICE_EPICOINS:,} 🪙 или {REROLL_PRICE_RESOURCES:,} 🧬\n"
            f"🧬 У вас: {lab['bio_resource']:,} 🧬 / {lab['epicoins']:,} 🪙",
            show_alert=True
        )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            if use_epicoins:
                await cur.execute(
                    "UPDATE Lab SET epicoins = epicoins - %s WHERE lab_id = %s",
                    (REROLL_PRICE_EPICOINS, user_id)
                )
                spent = f"{REROLL_PRICE_EPICOINS:,} 🪙"
            else:
                await cur.execute(
                    "UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s",
                    (REROLL_PRICE_RESOURCES, user_id)
                )
                spent = f"{REROLL_PRICE_RESOURCES:,} 🧬"

    await reset_acts(redis, user_id)
    await call.answer(f"🔄 Акции обновлены! Списано: {spent}", show_alert=True)

    text, kb = await build_acts_text(pool, redis, user_id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[ACTS REROLL ERROR] {e}")


@router.callback_query(F.data == "acts_menu")
async def cb_acts_menu(call: CallbackQuery, pool: Pool, redis: Redis):
    user_id = call.from_user.id

    # Загружаем lab_info для исключения science >= 55
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT science, pathogens, ready_pathogens FROM Lab WHERE lab_id = %s",
                (user_id,)
            )
            lab_info = await cur.fetchone()

    # Если Redis пуст — генерируем с учётом lab_info
    key = f"discount:{user_id}"
    if not await redis.get(key):
        await get_acts(redis, user_id, lab_info)

    text, kb = await build_acts_text(pool, redis, user_id)

    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[ACTS MENU ERROR] {e}")
    await call.answer()


# ===== ХЕНДЛЕР: ПОКУПКА ЛОТА =====
@router.callback_query(F.data.startswith("act:buy:"))
async def cb_act_buy(call: CallbackQuery, pool: Pool, redis: Redis):
    user_id = call.from_user.id
    act_num = int(call.data.split(":")[2])  # 1, 2 или 3

    acts_data = await get_acts(redis, user_id)
    acts = acts_data["acts"]

    if act_num < 1 or act_num > len(acts):
        return await call.answer("❌ Лот не найден", show_alert=True)

    act = acts[act_num - 1]

    # Проверка: куплено?
    if act["purchased"]:
        return await call.answer("❌ Уже куплено!", show_alert=True)

    # Цена
    base_price, final_price = await get_act_price(pool, user_id, act)

    # Проверка баланса
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT bio_resource, epicoins FROM Lab WHERE lab_id = %s",
                (user_id,)
            )
            lab = await cur.fetchone()

    if not lab:
        return await call.answer("❌ Нет лаборатории!", show_alert=True)

    if act["currency"] == "resources":
        if lab["bio_resource"] < final_price:
            return await call.answer(
                f"❌ Недостаточно ресурсов!\n"
                f"💰 Нужно: {final_price:,} 🧬\n"
                f"🧬 У вас: {lab['bio_resource']:,} 🧬",
                show_alert=True
            )
    else:  # epicoins
        if lab["epicoins"] < final_price:
            return await call.answer(
                f"❌ Недостаточно эпикоинов!\n"
                f"💰 Нужно: {final_price:,} 🪙\n"
                f"🪙 У вас: {lab['epicoins']:,} 🪙",
                show_alert=True
            )

    # ===== СПИСАНИЕ + НАЧИСЛЕНИЕ =====
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                if act["type"] == "skill":
                    skill_db = act["skill"]
                    levels = act["levels"]

                    if act["currency"] == "resources":
                        await cur.execute(
                            f"UPDATE Lab SET bio_resource = bio_resource - %s, "
                            f"{skill_db} = {skill_db} + %s WHERE lab_id = %s",
                            (final_price, levels, user_id)
                        )
                    else:
                        await cur.execute(
                            f"UPDATE Lab SET epicoins = epicoins - %s, "
                            f"{skill_db} = {skill_db} + %s WHERE lab_id = %s",
                            (final_price, levels, user_id)
                        )
                else:  # case
                    case_col = "case1" if act["case_type"] == "case1" else "case2"

                    if act["currency"] == "resources":
                        await cur.execute(
                            f"UPDATE Lab SET bio_resource = bio_resource - %s, "
                            f"{case_col} = {case_col} + 1 WHERE lab_id = %s",
                            (final_price, user_id)
                        )
                    else:
                        await cur.execute(
                            f"UPDATE Lab SET epicoins = epicoins - %s, "
                            f"{case_col} = {case_col} + 1 WHERE lab_id = %s",
                            (final_price, user_id)
                        )

        # Помечаем как купленную
        act["purchased"] = True
        await save_acts(redis, user_id, acts_data)

        await call.answer("✅ Куплено!", show_alert=True)

        # Обновляем сообщение
        text, kb = await build_acts_text(pool, redis, user_id)
        try:
            await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                print(f"[ACTS EDIT ERROR] {e}")

    except Exception as e:
        print(f"[ACT BUY ERROR] {e}")
        await call.answer(f"❌ Ошибка: {e}", show_alert=True)

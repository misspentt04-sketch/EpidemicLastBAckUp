import json
import random
import time
import asyncio
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor
from redis.asyncio import Redis

router = Router()

# ===== НАСТРОЙКИ =====
ADMIN_ID = 7972320837
CHANNEL_ID = -1004493493697    # канал (подписка)
CHAT_ID = -1004335676077       # чат (состоит)
LOG_CHANNEL = -1004335676077   # куда постить розыгрыши
MAX_MEMBERS = 50
MAX_HOURS = 6
MIN_WINNERS = 3
MAX_WINNERS = 10

PRIZE_TYPES = {
    "resource": "🧬 Ресурсы",
    "epicoins": "🪙 Эпикоины",
    "case1": "📦 Кейсы",
    "case2": "💎 Донат-кейсы",
    "mix": "🎁 Всё вместе",
}


class GiveawayStates(StatesGroup):
    waiting_winners = State()
    waiting_prizes = State()
    confirming = State()


# ===== ПРОВЕРКА ПОДПИСКИ =====
async def check_member(bot: Bot, user_id: int) -> tuple[bool, str]:
    """Проверяет подписку на канал и участие в чате"""
    try:
        member_channel = await bot.get_chat_member(CHANNEL_ID, user_id)
        if member_channel.status in ("left", "kicked", "banned"):
            return False, f"❌ Вы не подписаны на канал!"
    except Exception:
        return False, f"❌ Ошибка проверки канала. Убедитесь, что бот — админ в канале."

    try:
        member_chat = await bot.get_chat_member(CHAT_ID, user_id)
        if member_chat.status in ("left", "kicked", "banned"):
            return False, f"❌ Вы не состоите в чате!"
    except Exception:
        return False, f"❌ Ошибка проверки чата. Убедитесь, что бот — админ в чате."

    return True, ""


# ===== МЕНЮ =====
@router.message(F.text.lower() == "!розыгрыш")
async def cmd_giveaway(msg: Message, redis: Redis):
    # ===== ТОЛЬКО АДМИН =====
    if msg.from_user.id != ADMIN_ID:
        return

    # ===== КД 12 ЧАСОВ =====
    cooldown_key = f"giveaway_cooldown:{msg.from_user.id}"
    last = await redis.get(cooldown_key)
    if last:
        remaining = 12 * 3600 - (int(time.time()) - int(last))
        if remaining > 0:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return await msg.reply(
                f"⏳ <b>КД на создание розыгрыша!</b>\n\n"
                f"Осталось: <b>{hours}ч {minutes}м</b>\n"
                f"Следующий розыгрыш можно создать через 12 часов после предыдущего.",
                parse_mode="HTML"
            )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧬 Ресурсы", callback_data="gw:type:resource")],
        [InlineKeyboardButton(text="🪙 Эпикоины", callback_data="gw:type:epicoins")],
        [InlineKeyboardButton(text="📦 Кейсы", callback_data="gw:type:case1")],
        [InlineKeyboardButton(text="💎 Донат-кейсы", callback_data="gw:type:case2")],
        [InlineKeyboardButton(text="🎁 Всё вместе", callback_data="gw:type:mix")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="gw:cancel")],
    ])
    await msg.reply(
        "🎁 <b>Создание розыгрыша</b>\n\nВыберите тип приза:",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "gw:cancel")
async def gw_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Розыгрыш отменён.")
    await call.answer()


# ===== ВЫБОР ТИПА =====
@router.callback_query(F.data.startswith("gw:type:"))
async def gw_type(call: CallbackQuery, state: FSMContext):
    prize_type = call.data.split(":")[2]
    await state.update_data(prize_type=prize_type, creator_id=call.from_user.id)
    await state.set_state(GiveawayStates.waiting_winners)

    await call.message.edit_text(
        f"🎁 <b>Тип приза:</b> {PRIZE_TYPES[prize_type]}\n\n"
        f"Сколько победителей? (от {MIN_WINNERS} до {MAX_WINNERS})\n"
        f"Введите число:",
        parse_mode="HTML"
    )
    await call.answer()


# ===== КОЛИЧЕСТВО ПОБЕДИТЕЛЕЙ =====
@router.message(GiveawayStates.waiting_winners)
async def gw_winners(msg: Message, state: FSMContext):
    if msg.text and msg.text.strip().lower() in ("отмена", "cancel", "стоп"):
        await state.clear()
        return await msg.reply("❌ Создание розыгрыша отменено.")

    try:
        count = int(msg.text.strip())
    except ValueError:
        return await msg.reply(f"❌ Введите число от {MIN_WINNERS} до {MAX_WINNERS}")

    if count < MIN_WINNERS or count > MAX_WINNERS:
        return await msg.reply(f"❌ Число должно быть от {MIN_WINNERS} до {MAX_WINNERS}")

    data = await state.get_data()
    prize_type = data["prize_type"]
    await state.update_data(winners_count=count, current_place=1, prizes=[])
    await state.set_state(GiveawayStates.waiting_prizes)

    await msg.reply(
        f"✅ Победителей: <b>{count}</b>\n\n"
        f"🎁 Введите приз за <b>1 место</b>:",
        parse_mode="HTML"
    )


# ===== ПРИЗЫ ПО МЕСТАМ =====
@router.message(GiveawayStates.waiting_prizes)
async def gw_prizes(msg: Message, state: FSMContext, pool: Pool, bot: Bot, redis: Redis):
    if msg.text and msg.text.strip().lower() in ("отмена", "cancel", "стоп"):
        await state.clear()
        return await msg.reply("❌ Создание розыгрыша отменено.")

    data = await state.get_data()
    prize_type = data["prize_type"]
    current_place = data["current_place"]
    winners_count = data["winners_count"]
    prizes = data["prizes"]

    text = msg.text.strip()

    # Парсинг приза
    if prize_type == "mix":
        # Умный парсер: "1000000 ресурсы 5 дк" или "1000000 500 5 2"
        import re
        text_lower = text.lower()

        # Заменяем ключевые слова на числа-маркеры
        resource = 0
        epicoins = 0
        case1 = 0
        case2 = 0

        # Ищем паттерны: число + слово
        # "1000000 ресурсы", "1000000 ресурсов", "1000000 р"
        m = re.search(r'(\d+)\s*(?:ресурс|ресурсов|р\b|🧬)', text_lower)
        if m:
            resource = int(m.group(1))

        # "500 коины", "500 коинов", "500 эпикоинов", "500 🪙"
        m = re.search(r'(\d+)\s*(?:коин|коинов|эпикоин|эпикоинов|🪙)', text_lower)
        if m:
            epicoins = int(m.group(1))

        # "5 кейсы", "5 кейсов", "5 📦"
        m = re.search(r'(\d+)\s*(?:кейс|кейсов|📦)', text_lower)
        if m:
            case1 = int(m.group(1))

        # "2 дк", "2 донат", "2 донат-кейсов", "2 💎"
        m = re.search(r'(\d+)\s*(?:дк|донат|донатных|💎)', text_lower)
        if m:
            case2 = int(m.group(1))

        # Если ничего не нашли — пробуем как 4 числа
        if resource == 0 and epicoins == 0 and case1 == 0 and case2 == 0:
            parts = text.split()
            if len(parts) == 4:
                try:
                    resource, epicoins, case1, case2 = map(int, parts)
                except ValueError:
                    return await msg.reply(
                        "❌ Не понял формат.\n\n"
                        "<b>Варианты:</b>\n"
                        "1) <code>1000000 500 5 2</code> (4 числа)\n"
                        "2) <code>1000000 ресурсы 500 коины 5 кейсы 2 дк</code>\n"
                        "3) <code>1000000🧬 500🪙 5📦 2💎</code>",
                        parse_mode="HTML"
                    )
            else:
                return await msg.reply(
                    "❌ Не понял формат.\n\n"
                    "<b>Варианты:</b>\n"
                    "1) <code>1000000 500 5 2</code> (4 числа)\n"
                    "2) <code>1000000 ресурсы 500 коины 5 кейсы 2 дк</code>\n"
                    "3) <code>1000000🧬 500🪙 5📦 2💎</code>",
                    parse_mode="HTML"
                )

        prize = {"place": current_place, "resource": resource, "epicoins": epicoins, "case1": case1, "case2": case2}
    else:
        try:
            amount = int(text)
        except ValueError:
            return await msg.reply("❌ Введите число")
        prize = {"place": current_place, "resource": 0, "epicoins": 0, "case1": 0, "case2": 0}
        prize[prize_type] = amount

    prizes.append(prize)

    if current_place < winners_count:
        await state.update_data(prizes=prizes, current_place=current_place + 1)
        await msg.reply(f"🎁 Введите приз за <b>{current_place + 1} место</b>:", parse_mode="HTML")
        return

    # Всё готово — показываем итог и подтверждение
    await state.update_data(prizes=prizes)

    # Формируем список призов
    lines = ["🎁 <b>Проверьте награды:</b>\n"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for p in prizes:
        place = p["place"]
        parts = []
        if p.get("resource", 0) > 0:
            parts.append(f"{p['resource']:,} 🧬")
        if p.get("epicoins", 0) > 0:
            parts.append(f"{p['epicoins']:,} 🪙")
        if p.get("case1", 0) > 0:
            parts.append(f"{p['case1']} 📦")
        if p.get("case2", 0) > 0:
            parts.append(f"{p['case2']} 💎")

        if not parts:
            parts = ["ничего"]

        medal = medals[place - 1] if place <= len(medals) else f"{place}."
        lines.append(f"{medal} {place} место — {', '.join(parts)}")

    lines.append("\n✅ Всё верно? Нажмите «Подтвердить».")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="gw:confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="gw:cancel_prizes")],
    ])

    await state.set_state(GiveawayStates.confirming)
    await msg.reply("\n".join(lines), reply_markup=kb, parse_mode="HTML")


# ===== СОЗДАНИЕ РОЗЫГРЫША =====
async def create_giveaway(msg: Message, state: FSMContext, pool: Pool, bot: Bot, redis: Redis):
    data = await state.get_data()
    prize_type = data["prize_type"]
    winners_count = data["winners_count"]
    prizes = data["prizes"]
    creator_id = data.get("creator_id") or msg.from_user.id

    end_time = int(time.time()) + MAX_HOURS * 3600

    # ===== СЧИТАЕМ ОБЩУЮ СУММУ ПРИЗОВ =====
    total_resource = sum(p.get("resource", 0) for p in prizes)
    total_epicoins = sum(p.get("epicoins", 0) for p in prizes)
    total_case1 = sum(p.get("case1", 0) for p in prizes)
    total_case2 = sum(p.get("case2", 0) for p in prizes)

    # ===== ПРОВЕРЯЕМ БАЛАНС =====
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT bio_resource, epicoins, case1, case2 FROM Lab WHERE lab_id = %s",
                (creator_id,)
            )
            lab = await cur.fetchone()

    if not lab:
        await state.clear()
        return await msg.reply("❌ У вас нет лаборатории!")

    if lab["bio_resource"] < total_resource:
        await state.clear()
        return await msg.reply(f"❌ Не хватает ресурсов! Нужно <b>{total_resource:,}</b> 🧬, у вас <b>{lab['bio_resource']:,}</b>", parse_mode="HTML")
    if lab["epicoins"] < total_epicoins:
        await state.clear()
        return await msg.reply(f"❌ Не хватает эпикоинов! Нужно <b>{total_epicoins:,}</b> 🪙, у вас <b>{lab['epicoins']:,}</b>", parse_mode="HTML")
    if lab["case1"] < total_case1:
        await state.clear()
        return await msg.reply(f"❌ Не хватает кейсов! Нужно <b>{total_case1}</b> 📦, у вас <b>{lab['case1']}</b>", parse_mode="HTML")
    if lab["case2"] < total_case2:
        await state.clear()
        return await msg.reply(f"❌ Не хватает донат-кейсов! Нужно <b>{total_case2}</b> 💎, у вас <b>{lab['case2']}</b>", parse_mode="HTML")

    # ===== СПИСЫВАЕМ =====
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                UPDATE Lab
                SET bio_resource = bio_resource - %s,
                    epicoins = epicoins - %s,
                    case1 = case1 - %s,
                    case2 = case2 - %s
                WHERE lab_id = %s
            """, (total_resource, total_epicoins, total_case1, total_case2, creator_id))

    # ===== СОЗДАЁМ РОЗЫГРЫШ =====
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO Giveaways (creator_id, prize_type, winners_count, prizes, end_time)
                   VALUES (%s, %s, %s, %s, %s)""",
                (creator_id, prize_type, winners_count, json.dumps(prizes), end_time)
            )
            giveaway_id = cur.lastrowid

    # Пост в канал
    text = (
        f"🎁 <b>РОЗЫГРЫШ!</b>\n\n"
        f"🎯 Тип: {PRIZE_TYPES[prize_type]}\n"
        f"🏆 Победителей: <b>{winners_count}</b>\n"
        f"⏳ До 6 часов или 50 участников\n\n"
        f"Нажмите кнопку ниже, чтобы участвовать!"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 Участвовать", callback_data=f"gw:join:{giveaway_id}")],
    ])

    try:
        sent = await bot.send_message(LOG_CHANNEL, text, reply_markup=kb, parse_mode="HTML")
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE Giveaways SET channel_msg_id = %s WHERE id = %s", (sent.message_id, giveaway_id))
    except Exception as e:
        await msg.reply(f"❌ Ошибка поста в канал: {e}")
        return

    await state.clear()
    await msg.reply(f"✅ Розыгрыш создан! ID: <code>{giveaway_id}</code>", parse_mode="HTML")


# ===== УЧАСТИЕ =====
@router.callback_query(F.data.startswith("gw:join:"))
async def gw_join(call: CallbackQuery, pool: Pool, bot: Bot):
    giveaway_id = int(call.data.split(":")[2])
    user_id = call.from_user.id

    # Проверка подписки
    ok, err = await check_member(bot, user_id)
    if not ok:
        return await call.answer(err, show_alert=True)

    # Проверка, что розыгрыш активен
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT is_finished, end_time FROM Giveaways WHERE id = %s", (giveaway_id,))
            gw = await cur.fetchone()
            if not gw or gw[0] == 1 or gw[1] < time.time():
                return await call.answer("❌ Розыгрыш завершён!", show_alert=True)

            # Проверка лимита
            await cur.execute("SELECT COUNT(*) FROM GiveawayMembers WHERE giveaway_id = %s", (giveaway_id,))
            count = (await cur.fetchone())[0]
            if count >= MAX_MEMBERS:
                return await call.answer("❌ Участников уже 50!", show_alert=True)

            # Добавляем
            try:
                await cur.execute(
                    "INSERT INTO GiveawayMembers (giveaway_id, user_id) VALUES (%s, %s)",
                    (giveaway_id, user_id)
                )
                await call.answer("✅ Вы участвуете!", show_alert=True)
            except Exception:
                return await call.answer("❌ Вы уже участвуете!", show_alert=True)

    # TODO: обновить счётчик в сообщении


# ===== СПИСОК УЧАСТНИКОВ =====
@router.callback_query(F.data.startswith("gw:members:"))
async def gw_members_old(call: CallbackQuery):
    await call.answer("❌ Кнопка устарела", show_alert=True)


# ===== ПОДТВЕРЖДЕНИЕ РОЗЫГРЫША =====
@router.callback_query(F.data == "gw:confirm")
async def gw_confirm(call: CallbackQuery, state: FSMContext, pool: Pool, bot: Bot, redis: Redis):
    data = await state.get_data()
    if not data or "prizes" not in data:
        await call.answer("❌ Данные потеряны", show_alert=True)
        await state.clear()
        return

    await call.message.edit_text("⏳ Создаю розыгрыш...")
    await create_giveaway(call.message, state, pool, bot, redis)
    await call.answer("✅ Розыгрыш создан!")


# ===== ОТМЕНА НА ЭТАПЕ ПОДТВЕРЖДЕНИЯ =====
@router.callback_query(F.data == "gw:cancel_prizes")
async def gw_cancel_prizes(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Создание розыгрыша отменено.")
    await call.answer()

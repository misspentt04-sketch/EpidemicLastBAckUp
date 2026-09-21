"""
Обмен валют: 🪙 ↔ 🧬
Цена привязана к доходу с жертв за тик:
  Покупка 1 🪙 = 0.5% от дохода за тик (мин 5 000 🧬)
  Продажа 1 🪙 = 0.01% от дохода за тик (мин 100 🧬)
Минимум для обмена: доход ≥ 1 000 000 🧬 / тик
"""
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor


router = Router()


# ===== НАСТРОЙКИ =====
BUY_PERCENT = 0.005      # 0.5% от дохода за тик
SELL_PERCENT = 0.0001    # 0.01% от дохода за тик

MIN_BUY_PRICE = 5_000       # мин цена покупки 1 🪙
MIN_SELL_PRICE = 100        # мин цена продажи 1 🪙

MIN_INCOME = 1_000_000      # минимальный доход за тик для доступа к обмену

MIN_BUY_EPICOINS = 1
MIN_SELL_EPICOINS = 1


class ExchangeStates(StatesGroup):
    waiting_buy = State()
    waiting_sell = State()


async def get_income_per_tick(pool: Pool, user_id: int) -> int:
    """Считает доход с жертв за 1 тик (как в force_tick)"""
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT 
                    COALESCE(SUM(v.victim_bio_resource_earn), 0) * 
                    (1 + COALESCE(l.rebirth_level, 0) * 0.10) AS income
                FROM Victims v
                LEFT JOIN Lab l ON l.lab_id = v.victims_owner_id
                WHERE v.victims_owner_id = %s
                GROUP BY v.victims_owner_id
            """, (user_id,))
            row = await cur.fetchone()
            if not row or not row["income"]:
                return 0
            return int(row["income"])


async def get_prices(pool: Pool, user_id: int):
    """Возвращает (buy_price, sell_price, income).
    buy_price == 0 → обмен недоступен.
    """
    income = await get_income_per_tick(pool, user_id)
    if income < MIN_INCOME:
        return 0, 0, income
    buy_price = max(MIN_BUY_PRICE, int(income * BUY_PERCENT))
    sell_price = max(MIN_SELL_PRICE, int(income * SELL_PERCENT))
    return buy_price, sell_price, income


def get_exchange_menu(buy_price: int, sell_price: int):
    if buy_price == 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Недоступно", callback_data="exchange:unavailable")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="shop_back")],
        ])
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💰 Купить 🪙 за {buy_price:,} 🧬",
                callback_data="exchange:buy"
            )],
            [InlineKeyboardButton(
                text=f"💸 Продать 🪙 за {sell_price:,} 🧬",
                callback_data="exchange:sell"
            )],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="shop_back")],
        ])
    return kb


def get_cancel_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="exchange:cancel")],
    ])


@router.callback_query(F.data == "exchange:unavailable")
async def cb_exchange_unavailable(call: CallbackQuery):
    await call.answer(
        f"🚫 Обмен недоступен!\nНужен доход ≥ {MIN_INCOME:,} 🧬 / тик",
        show_alert=True
    )


# ===== МЕНЮ ОБМЕНА =====
@router.callback_query(F.data == "exchange_menu")
async def cb_exchange_menu(call: CallbackQuery, pool: Pool, state: FSMContext):
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

    buy_price, sell_price, income = await get_prices(pool, user_id)

    if income < MIN_INCOME:
        text = (
            f"💱 <b>Обмен валют</b>\n\n"
            f"💰 <b>Ваш баланс:</b>\n"
            f"🪙 Эпикоины: <b>{lab['epicoins']:,}</b>\n"
            f"🧬 Ресурсы: <b>{lab['bio_resource']:,}</b>\n\n"
            f"📈 <b>Доход с жертв за тик:</b> <b>{income:,} 🧬</b>\n\n"
            f"🚫 <b>Обмен недоступен!</b>\n\n"
            f"📊 Требуется доход <b>{MIN_INCOME:,} 🧬</b> / тик\n"
            f"У вас: <b>{income:,} 🧬</b> / тик\n\n"
            f"💡 Зараждайте больше жертв, чтобы получить доступ!"
        )
    else:
        text = (
            f"💱 <b>Обмен валют</b>\n\n"
            f"💰 <b>Ваш баланс:</b>\n"
            f"🪙 Эпикоины: <b>{lab['epicoins']:,}</b>\n"
            f"🧬 Ресурсы: <b>{lab['bio_resource']:,}</b>\n\n"
            f"📈 <b>Доход с жертв за тик:</b> <b>{income:,} 🧬</b>\n\n"
            f"📊 <b>Курс (от дохода):</b>\n"
            f"💰 Купить 1 🪙 — <b>{buy_price:,} 🧬</b>\n"
            f"💸 Продать 1 🪙 — <b>{sell_price:,} 🧬</b>\n\n"
            f"👇 Выберите операцию:"
        )

    try:
        await call.message.edit_text(
            text,
            reply_markup=get_exchange_menu(buy_price, sell_price),
            parse_mode="HTML"
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"[EXCHANGE MENU ERROR] {e}")
    await call.answer()


# ===== КУПИТЬ =====
@router.callback_query(F.data == "exchange:buy")
async def cb_exchange_buy(call: CallbackQuery, pool: Pool, state: FSMContext):
    user_id = call.from_user.id
    buy_price, _, income = await get_prices(pool, user_id)

    if buy_price == 0:
        return await call.answer(
            f"🚫 Обмен недоступен! Нужен доход ≥ {MIN_INCOME:,} 🧬 / тик",
            show_alert=True
        )

    await state.set_state(ExchangeStates.waiting_buy)
    await call.message.edit_text(
        f"💰 <b>Купить эпикоины</b>\n\n"
        f"📈 Доход за тик: <b>{income:,} 🧬</b>\n"
        f"💵 Цена: <b>{buy_price:,} 🧬</b> за <b>1 🪙</b>\n\n"
        f"Введите, <b>сколько 🪙 купить</b>:\n"
        f"Пример: <code>10</code>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )
    await call.answer()


# ===== ПРОДАТЬ =====
@router.callback_query(F.data == "exchange:sell")
async def cb_exchange_sell(call: CallbackQuery, pool: Pool, state: FSMContext):
    user_id = call.from_user.id
    _, sell_price, income = await get_prices(pool, user_id)

    if sell_price == 0:
        return await call.answer(
            f"🚫 Обмен недоступен! Нужен доход ≥ {MIN_INCOME:,} 🧬 / тик",
            show_alert=True
        )

    await state.set_state(ExchangeStates.waiting_sell)
    await call.message.edit_text(
        f"💸 <b>Продать эпикоины</b>\n\n"
        f"📈 Доход за тик: <b>{income:,} 🧬</b>\n"
        f"💵 Цена: <b>{sell_price:,} 🧬</b> за <b>1 🪙</b>\n\n"
        f"Введите, <b>сколько 🪙 продать</b>:\n"
        f"Пример: <code>10</code>",
        reply_markup=get_cancel_menu(),
        parse_mode="HTML"
    )
    await call.answer()


# ===== ОТМЕНА =====
@router.callback_query(F.data == "exchange:cancel")
async def cb_exchange_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.delete()
    except:
        pass
    await call.answer("❌ Отменено")
    try:
        from core.handlers.biowar.donates.cases import get_cases_keyboard
        await call.message.answer(
            "🎁 <b>Меню кейсов</b>",
            reply_markup=get_cases_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[EXCHANGE CANCEL ERROR] {e}")


# ===== ПОКУПКА =====
@router.message(ExchangeStates.waiting_buy)
async def process_buy(msg: Message, state: FSMContext, pool: Pool):
    if msg.text and msg.text.strip().lower() in ("отмена", "cancel", "стоп"):
        await state.clear()
        return await msg.reply("❌ Обмен отменён.")

    try:
        amount = int(msg.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        return await msg.reply("❌ Введите целое число!")

    if amount < MIN_BUY_EPICOINS:
        return await msg.reply(f"❌ Минимум: <b>{MIN_BUY_EPICOINS} 🪙</b>", parse_mode="HTML")

    user_id = msg.from_user.id
    buy_price, _, income = await get_prices(pool, user_id)

    if buy_price == 0:
        await state.clear()
        return await msg.reply(
            f"🚫 Обмен недоступен! Нужен доход ≥ {MIN_INCOME:,} 🧬 / тик",
            parse_mode="HTML"
        )

    total_cost = amount * buy_price

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT bio_resource FROM Lab WHERE lab_id = %s",
                (user_id,)
            )
            lab = await cur.fetchone()

    if not lab:
        await state.clear()
        return await msg.reply("❌ Нет лаборатории!")

    if lab["bio_resource"] < total_cost:
        return await msg.reply(
            f"❌ Недостаточно ресурсов!\n"
            f"Нужно: <b>{total_cost:,}</b> 🧬\n"
            f"У вас: <b>{lab['bio_resource']:,}</b> 🧬",
            parse_mode="HTML"
        )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE Lab SET bio_resource = bio_resource - %s, epicoins = epicoins + %s WHERE lab_id = %s",
                (total_cost, amount, user_id)
            )

    await state.clear()

    await msg.reply(
        f"✅ <b>Куплено!</b>\n\n"
        f"📥 Получено: <b>+{amount:,} 🪙</b>\n"
        f"💸 Списано: <b>−{total_cost:,} 🧬</b>\n\n"
        f"💵 Цена: {buy_price:,} 🧬 за 1 🪙\n"
        f"📈 Доход за тик: {income:,} 🧬",
        parse_mode="HTML"
    )


# ===== ПРОДАЖА =====
@router.message(ExchangeStates.waiting_sell)
async def process_sell(msg: Message, state: FSMContext, pool: Pool):
    if msg.text and msg.text.strip().lower() in ("отмена", "cancel", "стоп"):
        await state.clear()
        return await msg.reply("❌ Обмен отменён.")

    try:
        amount = int(msg.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        return await msg.reply("❌ Введите целое число!")

    if amount < MIN_SELL_EPICOINS:
        return await msg.reply(f"❌ Минимум: <b>{MIN_SELL_EPICOINS} 🪙</b>", parse_mode="HTML")

    user_id = msg.from_user.id
    _, sell_price, income = await get_prices(pool, user_id)

    if sell_price == 0:
        await state.clear()
        return await msg.reply(
            f"🚫 Обмен недоступен! Нужен доход ≥ {MIN_INCOME:,} 🧬 / тик",
            parse_mode="HTML"
        )

    total_gain = amount * sell_price

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT epicoins FROM Lab WHERE lab_id = %s",
                (user_id,)
            )
            lab = await cur.fetchone()

    if not lab:
        await state.clear()
        return await msg.reply("❌ Нет лаборатории!")

    if lab["epicoins"] < amount:
        return await msg.reply(
            f"❌ Недостаточно эпикоинов!\n"
            f"Нужно: <b>{amount:,}</b> 🪙\n"
            f"У вас: <b>{lab['epicoins']:,}</b> 🪙",
            parse_mode="HTML"
        )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE Lab SET epicoins = epicoins - %s, bio_resource = bio_resource + %s WHERE lab_id = %s",
                (amount, total_gain, user_id)
            )

    await state.clear()

    await msg.reply(
        f"✅ <b>Продано!</b>\n\n"
        f"📤 Списано: <b>−{amount:,} 🪙</b>\n"
        f"📥 Получено: <b>+{total_gain:,} 🧬</b>\n\n"
        f"💵 Цена: {sell_price:,} 🧬 за 1 🪙\n"
        f"📈 Доход за тик: {income:,} 🧬",
        parse_mode="HTML"
    )

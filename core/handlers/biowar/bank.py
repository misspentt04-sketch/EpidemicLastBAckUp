import time
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor

router = Router()

# ===== НАСТРОЙКИ БАНКА =====
DEPOSIT_DAILY = 15.0
DEPOSIT_HOURLY = DEPOSIT_DAILY / 24

CREDIT_BASE = 50.0
CREDIT_DAILY = 50.0
CREDIT_HOURLY = CREDIT_DAILY / 24

CREDIT_TERM = 7 * 86400
CREDIT_PENALTY = 5

class BankStates(StatesGroup):
    waiting_deposit_amount = State()
    waiting_credit_amount = State()

# ===== ФУНКЦИИ =====
async def get_bank(pool: Pool, user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("SELECT * FROM Bank WHERE user_id = %s", (user_id,))
            return await cur.fetchone()

async def create_bank(pool: Pool, user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("INSERT IGNORE INTO Bank (user_id) VALUES (%s)", (user_id,))

async def get_balance(pool: Pool, user_id: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            if row:
                return row.get('bio_resource', 0) or 0
            return 0

async def get_tick_income(pool: Pool, user_id: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT COALESCE(SUM(victim_bio_resource_earn), 0) as total
                FROM Victims
                WHERE victims_owner_id = %s
            """, (user_id,))
            row = await cur.fetchone()
            if row:
                return int(row.get('total', 0) or 0)
            return 0

def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")

def calculate_credit_debt(credit_amount: int, credit_start: int) -> int:
    if credit_amount <= 0:
        return 0
    now = int(time.time())
    hours = (now - credit_start) / 3600
    percent = CREDIT_BASE + (CREDIT_HOURLY * hours)
    return int(credit_amount * (1 + percent / 100))

def calculate_deposit_income(deposit_amount: int, deposit_start: int) -> int:
    if deposit_amount <= 0:
        return 0
    now = int(time.time())
    hours = (now - deposit_start) / 3600
    return int(deposit_amount * (DEPOSIT_HOURLY / 100) * hours)

# ===== МЕНЮ =====
async def send_bank_menu(target, pool: Pool, user_id: int, is_callback: bool = False):
    bank = await get_bank(pool, user_id)
    if not bank:
        await create_bank(pool, user_id)
        bank = await get_bank(pool, user_id)

    if isinstance(bank, dict):
        deposit_amount = bank.get('deposit_amount', 0) or 0
        deposit_start = bank.get('deposit_start', 0) or 0
        credit_amount = bank.get('credit_amount', 0) or 0
        credit_start = bank.get('credit_start', 0) or 0
        credit_expire = bank.get('credit_expire', 0) or 0
        credit_returned = bank.get('credit_returned', 0) or 0
        total_earned = bank.get('total_earned', 0) or 0
        total_borrowed = bank.get('total_borrowed', 0) or 0
    else:
        deposit_amount = bank[2] if len(bank) > 2 else 0
        deposit_start = bank[3] if len(bank) > 3 else 0
        credit_amount = bank[5] if len(bank) > 5 else 0
        credit_start = bank[6] if len(bank) > 6 else 0
        credit_expire = bank[8] if len(bank) > 8 else 0
        credit_returned = bank[9] if len(bank) > 9 else 0
        total_earned = bank[11] if len(bank) > 11 else 0
        total_borrowed = bank[12] if len(bank) > 12 else 0

    balance = await get_balance(pool, user_id)
    tick_income = await get_tick_income(pool, user_id)
    max_credit = tick_income * 10
    now = int(time.time())

    if deposit_amount > 0:
        deposit_time = now - deposit_start
        days = deposit_time // 86400
        hours = (deposit_time % 86400) // 3600
        income = calculate_deposit_income(deposit_amount, deposit_start)
        deposit_text = (
            f"💰 <b>Депозит:</b> {format_money(deposit_amount)} 🧬\n"
            f"📈 <b>Доход:</b> +{format_money(income)} 🧬\n"
            f"⏳ <b>Срок:</b> {days}д {hours}ч\n"
        )
    else:
        deposit_text = "💰 <b>Депозит:</b> пусто\n"

    if credit_amount > 0 and not credit_returned:
        debt = calculate_credit_debt(credit_amount, credit_start)
        time_left = credit_expire - now
        if time_left > 0:
            days_left = time_left // 86400
            hours_left = (time_left % 86400) // 3600
            current_percent = CREDIT_BASE + CREDIT_HOURLY * ((now - credit_start) / 3600)
            credit_text = (
                f"💳 <b>Кредит:</b> {format_money(credit_amount)} 🧬\n"
                f"📊 <b>К возврату:</b> {format_money(debt)} 🧬\n"
                f"📈 <b>Процент:</b> +{current_percent:.1f}%\n"
                f"⏳ <b>Осталось:</b> {days_left}д {hours_left}ч\n"
            )
        else:
            penalty = credit_amount * CREDIT_PENALTY
            credit_text = (
                f"💳 <b>Кредит:</b> {format_money(credit_amount)} 🧬\n"
                f"⚠️ <b>ПРОСРОЧЕН!</b> Штраф: -{format_money(penalty)} 🧬\n"
            )
    else:
        credit_text = "💳 <b>Кредит:</b> нет активных\n"

    text = (
        f"🏦 <b>БАНК ЭПИДЕМИИ</b>\n\n"
        f"💎 <b>Ваш баланс:</b> {format_money(balance)} 🧬\n"
        f"📊 <b>Доход с жертв:</b> {format_money(tick_income)} 🧬\n"
        f"💳 <b>Доступно кредита:</b> {format_money(max_credit)} 🧬 (×10 от дохода)\n\n"
        f"{deposit_text}\n"
        f"{credit_text}\n"
        f"📊 <b>Статистика:</b>\n"
        f"├ Всего заработано: +{format_money(total_earned)} 🧬\n"
        f"└ Всего взято в кредит: {format_money(total_borrowed)} 🧬\n\n"
        f"📋 <b>Условия:</b>\n"
        f"├ Депозит: +{DEPOSIT_DAILY}% в день ({DEPOSIT_HOURLY:.3f}%/час)\n"
        f"├ Кредит: +{CREDIT_BASE}% + растёт на {CREDIT_HOURLY:.3f}%/час\n"
        f"├ Максимум: ×10 от дохода\n"
        f"├ Лимит: после возврата\n"
        f"└ Штраф за просрочку: ×{CREDIT_PENALTY}\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Положить на депозит", callback_data="bank_deposit")],
        [InlineKeyboardButton(text="💳 Взять кредит", callback_data="bank_credit")],
        [InlineKeyboardButton(text="📤 Снять депозит", callback_data="bank_withdraw")],
        [InlineKeyboardButton(text="💸 Вернуть кредит", callback_data="bank_repay")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="bank_refresh")],
    ])

    if is_callback:
        try:
            await target.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    else:
        await target.reply(text, reply_markup=kb, parse_mode="HTML")

# ===== КОМАНДА БАНК =====
@router.message(F.text.lower().in_(["банк", "/bank"]))
async def cmd_bank(msg: Message, pool: Pool):
    await send_bank_menu(msg, pool, msg.from_user.id, is_callback=False)

# ===== ДЕПОЗИТ =====
@router.callback_query(F.data == "bank_deposit")
async def bank_deposit_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(BankStates.waiting_deposit_amount)
    await call.message.reply("💰 <b>Введите сумму для депозита:</b>", parse_mode="HTML")
    await call.answer()

@router.message(BankStates.waiting_deposit_amount)
async def bank_deposit_process(msg: Message, state: FSMContext, pool: Pool):
    await state.clear()
    try:
        amount = int(msg.text.strip())
        if amount <= 0:
            await msg.reply("❌ Сумма должна быть больше 0!")
            return

        balance = await get_balance(pool, msg.from_user.id)
        if balance < amount:
            await msg.reply(f"❌ Недостаточно средств! У вас {format_money(balance)} 🧬")
            return

        now = int(time.time())
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s", (amount, msg.from_user.id))
                await cur.execute("""
                    UPDATE Bank SET deposit_amount = deposit_amount + %s, deposit_start = %s, total_deposited = total_deposited + %s
                    WHERE user_id = %s
                """, (amount, now, amount, msg.from_user.id))

        await msg.reply(f"✅ Депозит {format_money(amount)} 🧬 оформлен!\n📈 Доход: +{DEPOSIT_DAILY}% в день", parse_mode="HTML")
    except ValueError:
        await msg.reply("❌ Введите число!")

# ===== КРЕДИТ =====
@router.callback_query(F.data == "bank_credit")
async def bank_credit_start(call: CallbackQuery, state: FSMContext, pool: Pool):
    user_id = call.from_user.id

    balance = await get_balance(pool, user_id)
    if balance < 0:
        await call.answer("❌ У вас минус! Сначала выйдите из минуса.", show_alert=True)
        return

    tick_income = await get_tick_income(pool, user_id)
    max_credit = tick_income * 10

    await state.set_state(BankStates.waiting_credit_amount)
    await call.message.reply(
        f"💳 <b>Введите сумму кредита:</b>\n\n"
        f"📊 Ваш доход: {format_money(tick_income)} 🧬\n"
        f"💰 Максимум: {format_money(max_credit)} 🧬 (×10)\n\n"
        f"📊 Базовый: +{CREDIT_BASE}%\n"
        f"📈 Рост: +{CREDIT_HOURLY:.2f}%/час\n"
        f"⏳ Срок: 7 дней",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(BankStates.waiting_credit_amount)
async def bank_credit_process(msg: Message, state: FSMContext, pool: Pool):
    await state.clear()
    try:
        amount = int(msg.text.strip())
        if amount <= 0:
            await msg.reply("❌ Сумма должна быть больше 0!")
            return

        user_id = msg.from_user.id

        balance = await get_balance(pool, user_id)
        if balance < 0:
            await msg.reply(
                f"❌ У вас отрицательный баланс: {format_money(balance)} 🧬\n"
                f"💸 Сначала выйдите из минуса, потом берите кредит.",
                parse_mode="HTML"
            )
            return

        tick_income = await get_tick_income(pool, user_id)
        max_credit = tick_income * 10

        if max_credit <= 0:
            await msg.reply(
                "❌ У вас нет дохода с жертв!\n"
                "Кредит выдаётся только игрокам с активными жертвами.",
                parse_mode="HTML"
            )
            return

        if amount > max_credit:
            await msg.reply(
                f"❌ Максимальная сумма кредита: {format_money(max_credit)} 🧬\n"
                f"📊 Ваш доход: {format_money(tick_income)} 🧬\n"
                f"📈 Лимит: ×10 от дохода",
                parse_mode="HTML"
            )
            return

        bank = await get_bank(pool, user_id)
        if isinstance(bank, dict):
            current_credit = bank.get('credit_amount', 0) or 0
            credit_returned = bank.get('credit_returned', 1)
        else:
            current_credit = bank[5] if len(bank) > 5 else 0
            credit_returned = bank[9] if len(bank) > 9 else 1

        if current_credit > 0 and not credit_returned:
            await msg.reply(
                "❌ У вас уже есть активный кредит!\n"
                "💸 Верните его, чтобы взять новый.",
                parse_mode="HTML"
            )
            return

        now = int(time.time())
        expire = now + CREDIT_TERM

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s", (amount, user_id))
                await cur.execute("""
                    UPDATE Bank SET credit_amount = %s, credit_start = %s, credit_expire = %s, credit_returned = 0, total_borrowed = total_borrowed + %s
                    WHERE user_id = %s
                """, (amount, now, expire, amount, user_id))

        debt = calculate_credit_debt(amount, now)
        await msg.reply(
            f"✅ <b>Кредит оформлен!</b>\n"
            f"💰 Сумма: {format_money(amount)} 🧬\n"
            f"📊 К возврату сейчас: {format_money(debt)} 🧬\n"
            f"📈 Растёт на +{CREDIT_HOURLY:.2f}%/час\n"
            f"⏳ Срок: 7 дней\n"
            f"⚠️ Следующий кредит: после возврата",
            parse_mode="HTML"
        )
    except ValueError:
        await msg.reply("❌ Введите число!")

# ===== СНЯТЬ ДЕПОЗИТ =====
@router.callback_query(F.data == "bank_withdraw")
async def bank_withdraw(call: CallbackQuery, pool: Pool):
    bank = await get_bank(pool, call.from_user.id)
    if isinstance(bank, dict):
        deposit_amount = bank.get('deposit_amount', 0) or 0
        deposit_start = bank.get('deposit_start', 0) or 0
    else:
        deposit_amount = bank[2] if len(bank) > 2 else 0
        deposit_start = bank[3] if len(bank) > 3 else 0

    if deposit_amount <= 0:
        await call.answer("❌ У вас нет депозита!", show_alert=True)
        return

    income = calculate_deposit_income(deposit_amount, deposit_start)
    total = deposit_amount + income

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s", (total, call.from_user.id))
            await cur.execute("UPDATE Bank SET deposit_amount = 0, deposit_start = 0, total_earned = total_earned + %s WHERE user_id = %s", (income, call.from_user.id))

    await call.answer(f"✅ Снято {format_money(total)} 🧬 (доход: +{format_money(income)})", show_alert=True)
    await send_bank_menu(call.message, pool, call.from_user.id, is_callback=True)

# ===== ВЕРНУТЬ КРЕДИТ =====
@router.callback_query(F.data == "bank_repay")
async def bank_repay(call: CallbackQuery, pool: Pool):
    bank = await get_bank(pool, call.from_user.id)
    if isinstance(bank, dict):
        credit_amount = bank.get('credit_amount', 0) or 0
        credit_start = bank.get('credit_start', 0) or 0
        credit_returned = bank.get('credit_returned', 1)
    else:
        credit_amount = bank[5] if len(bank) > 5 else 0
        credit_start = bank[6] if len(bank) > 6 else 0
        credit_returned = bank[9] if len(bank) > 9 else 1

    if credit_amount <= 0 or credit_returned:
        await call.answer("❌ У вас нет активного кредита!", show_alert=True)
        return

    debt = calculate_credit_debt(credit_amount, credit_start)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s", (debt, call.from_user.id))
            await cur.execute("UPDATE Bank SET credit_amount = 0, credit_returned = 1, total_repaid = total_repaid + %s WHERE user_id = %s", (debt, call.from_user.id))

    await call.answer(f"✅ Кредит возвращён! Списано {format_money(debt)} 🧬", show_alert=True)
    await send_bank_menu(call.message, pool, call.from_user.id, is_callback=True)

# ===== ОБНОВИТЬ =====
@router.callback_query(F.data == "bank_refresh")
async def bank_refresh(call: CallbackQuery, pool: Pool):
    await send_bank_menu(call.message, pool, call.from_user.id, is_callback=True)
    await call.answer("🔄 Обновлено!")

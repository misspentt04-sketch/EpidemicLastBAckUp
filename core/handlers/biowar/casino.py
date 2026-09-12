import random
import asyncio
import time
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor

router = Router()

# ===== ДОСТУП =====
YOUR_ID = 7972320837  # только этот ID может играть

# ===== НАСТРОЙКИ =====
MIN_BET_RESOURCE = 1000
MAX_BET_RESOURCE = 100_000_000
MIN_BET_CASE = 6
MAX_BET_CASE = 20
MIN_BET_EPICOINS = 10
MAX_BET_EPICOINS = 10_000_000

# ===== ШАНСЫ =====
CHANCES_RESOURCE = [
    {"chance": 38.0,  "mult": 0,    "name": "💀 Проигрыш",   "emoji": "💀"},
    {"chance": 7.0,   "mult": 0.25, "name": "💔 Обидно",     "emoji": "💔"},
    {"chance": 10.0,  "mult": 0.5,  "name": "😢 Мало",       "emoji": "😢"},
    {"chance": 15.0,  "mult": 1,    "name": "💰 Возврат",    "emoji": "💰"},
    {"chance": 15.0,  "mult": 1.5,  "name": "✨ Хорошо",     "emoji": "✨"},
    {"chance": 8.0,   "mult": 3,    "name": "⭐ Удача",      "emoji": "⭐"},
    {"chance": 4.0,   "mult": 5,    "name": "🔥 Огонь",      "emoji": "🔥"},
    {"chance": 3.0,   "mult": 10,   "name": "🎉 Джекпот",    "emoji": "🎉"},
]

CHANCES_CASE = [
    {"chance": 55.0,  "mult": 0,    "name": "💀 Проигрыш",   "emoji": "💀"},
    {"chance": 12.0,  "mult": 0.5,  "name": "💔 Обидно",     "emoji": "💔"},
    {"chance": 15.0,  "mult": 1,    "name": "😢 Возврат",    "emoji": "😢"},
    {"chance": 8.0,   "mult": 1.5,  "name": "✨ Хорошо",     "emoji": "✨"},
    {"chance": 5.0,   "mult": 2,    "name": "⭐ Удача",      "emoji": "⭐"},
    {"chance": 3.0,   "mult": 3,    "name": "🔥 Огонь",      "emoji": "🔥"},
    {"chance": 1.5,   "mult": 5,    "name": "💎 Богатство",  "emoji": "💎"},
    {"chance": 0.5,   "mult": 20,   "name": "🎉 Джекпот",    "emoji": "🎉"},
]

SLOT_EMOJIS = ["💀", "💔", "😢", "💰", "✨", "⭐", "🔥", "🎉", "💎", "🍀", "🎰", "🎲", "🃏", "👑", "💍"]

class CasinoStates(StatesGroup):
    waiting_bet_amount = State()

# ===== ФУНКЦИИ =====
async def get_balance(pool: Pool, user_id: int) -> int:
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            return (row.get('bio_resource', 0) or 0) if row else 0

async def get_assets(pool: Pool, user_id: int) -> dict:
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("SELECT case1, case2, epicoins FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            if row:
                return {
                    "case1": row.get('case1', 0) or 0,
                    "case2": row.get('case2', 0) or 0,
                    "epicoins": row.get('epicoins', 0) or 0,
                }
            return {"case1": 0, "case2": 0, "epicoins": 0}

def format_money(amount) -> str:
    if isinstance(amount, float):
        return f"{amount:,.2f}".replace(",", " ")
    return f"{amount:,}".replace(",", " ")

def roll_outcome(chances: list) -> dict:
    r = random.uniform(0, 100)
    cumulative = 0
    for outcome in chances:
        cumulative += outcome["chance"]
        if r <= cumulative:
            return outcome
    return chances[-1]

async def send_casino_menu(target, pool: Pool, user_id: int, is_callback: bool = False):
    balance = await get_balance(pool, user_id)
    assets = await get_assets(pool, user_id)
    
    text = (
        f"🎰 <b>КАЗИНО ЭПИДЕМИИ</b>\n\n"
        f"💎 <b>Ваш баланс:</b> {format_money(balance)} 🧬\n"
        f"🪙 <b>Эпикоины:</b> {format_money(assets['epicoins'])}\n"
        f"📦 <b>Обычные кейсы:</b> {assets['case1']}\n"
        f"💎 <b>Донатные кейсы:</b> {assets['case2']}\n\n"
        f"🎮 <b>Выберите тип ставки:</b>\n"
        f"├ 🧬 Ресурсы (от {format_money(MIN_BET_RESOURCE)})\n"
        f"├ 🪙 Эпикоины (от {MIN_BET_EPICOINS})\n"
        f"├ 📦 Обычные кейсы (от {MIN_BET_CASE} до {MAX_BET_CASE})\n"
        f"└ 💎 Донатные кейсы (от {MIN_BET_CASE} до {MAX_BET_CASE})\n\n"
        f"⚠️ <i>Играй ответственно! Казино всегда в плюсе 😉</i>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧬 Ресурсы", callback_data="casino_bet:resource")],
        [InlineKeyboardButton(text="🪙 Эпикоины", callback_data="casino_bet:epicoins")],
        [InlineKeyboardButton(text="📦 Обычные кейсы", callback_data="casino_bet:case1")],
        [InlineKeyboardButton(text="💎 Донатные кейсы", callback_data="casino_bet:case2")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="casino_refresh")],
    ])
    
    if is_callback:
        try:
            await target.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    else:
        await target.reply(text, reply_markup=kb, parse_mode="HTML")

# ===== КОМАНДА КАЗИНО (ТОЛЬКО ДЛЯ ТЕБЯ) =====
@router.message(F.text.lower().in_(["казино", "/casino"]))
async def cmd_casino(msg: Message, pool: Pool):
    await send_casino_menu(msg, pool, msg.from_user.id, is_callback=False)

# ===== ВЫБОР ТИПА СТАВКИ =====
@router.callback_query(F.data.startswith("casino_bet:"))
async def casino_bet_start(call: CallbackQuery, state: FSMContext, pool: Pool):
    
    bet_type = call.data.split(":")[1]
    user_id = call.from_user.id
    
    await state.set_state(CasinoStates.waiting_bet_amount)
    await state.update_data(bet_type=bet_type)
    
    balance = await get_balance(pool, user_id)
    assets = await get_assets(pool, user_id)
    
    if bet_type == "resource":
        text = (
            f"🧬 <b>Ставка ресурсами</b>\n\n"
            f"💎 Ваш баланс: {format_money(balance)} 🧬\n"
            f"📊 Лимиты: {format_money(MIN_BET_RESOURCE)} - {format_money(MAX_BET_RESOURCE)} 🧬\n\n"
            f"✍️ Введите сумму ставки:"
        )
    elif bet_type == "epicoins":
        text = (
            f"🪙 <b>Ставка эпикоинами</b>\n\n"
            f"🪙 У вас: {format_money(assets['epicoins'])}\n"
            f"📊 Лимиты: {MIN_BET_EPICOINS} - {format_money(MAX_BET_EPICOINS)}\n\n"
            f"✍️ Введите сумму ставки:"
        )
    elif bet_type == "case1":
        text = (
            f"📦 <b>Ставка обычными кейсами</b>\n\n"
            f"📦 У вас: {assets['case1']}\n"
            f"📊 Лимиты: {MIN_BET_CASE} - {MAX_BET_CASE}\n\n"
            f"✍️ Введите количество кейсов:"
        )
    elif bet_type == "case2":
        text = (
            f"💎 <b>Ставка донатными кейсами</b>\n\n"
            f"💎 У вас: {assets['case2']}\n"
            f"📊 Лимиты: {MIN_BET_CASE} - {MAX_BET_CASE}\n\n"
            f"✍️ Введите количество кейсов:"
        )
    else:
        await call.answer("❌ Неизвестный тип ставки!", show_alert=True)
        return
    
    await call.message.reply(text, parse_mode="HTML")
    await call.answer()

# ===== ОБРАБОТКА СТАВКИ =====
@router.message(CasinoStates.waiting_bet_amount)
async def casino_process_bet(msg: Message, state: FSMContext, pool: Pool):
    
    data = await state.get_data()
    bet_type = data.get('bet_type', 'resource')
    user_id = msg.from_user.id
    
    try:
        amount = int(msg.text.strip())
        if amount <= 0:
            await msg.reply("❌ Ставка должна быть больше 0!")
            return
        
        if bet_type == "resource":
            if amount < MIN_BET_RESOURCE:
                await msg.reply(f"❌ Минимальная ставка: {format_money(MIN_BET_RESOURCE)} 🧬")
                return
            if amount > MAX_BET_RESOURCE:
                await msg.reply(f"❌ Максимальная ставка: {format_money(MAX_BET_RESOURCE)} 🧬")
                return
            balance = await get_balance(pool, user_id)
            if balance < amount:
                await msg.reply(f"❌ Недостаточно средств! У вас {format_money(balance)} 🧬")
                return
            chances = CHANCES_RESOURCE
            unit = "🧬"
        
        elif bet_type == "epicoins":
            if amount < MIN_BET_EPICOINS:
                await msg.reply(f"❌ Минимальная ставка: {MIN_BET_EPICOINS} 🪙")
                return
            if amount > MAX_BET_EPICOINS:
                await msg.reply(f"❌ Максимальная ставка: {format_money(MAX_BET_EPICOINS)} 🪙")
                return
            assets = await get_assets(pool, user_id)
            if assets['epicoins'] < amount:
                await msg.reply(f"❌ Недостаточно эпикоинов! У вас {format_money(assets['epicoins'])}")
                return
            chances = CHANCES_RESOURCE
            unit = "🪙"
        
        elif bet_type in ("case1", "case2"):
            if amount < MIN_BET_CASE:
                await msg.reply(f"❌ Минимальная ставка: {MIN_BET_CASE} кейсов")
                return
            if amount > MAX_BET_CASE:
                await msg.reply(f"❌ Максимальная ставка: {MAX_BET_CASE} кейсов")
                return
            assets = await get_assets(pool, user_id)
            if assets[bet_type] < amount:
                await msg.reply(f"❌ Недостаточно кейсов! У вас {assets[bet_type]}")
                return
            chances = CHANCES_CASE
            unit = "📦" if bet_type == "case1" else "💎"
        
        else:
            await msg.reply("❌ Неизвестный тип ставки!")
            await state.clear()
            return
        
        await state.clear()
        
        # Списываем ставку
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                if bet_type == "resource":
                    await cur.execute("UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s", (amount, user_id))
                elif bet_type == "epicoins":
                    await cur.execute("UPDATE Lab SET epicoins = epicoins - %s WHERE lab_id = %s", (amount, user_id))
                elif bet_type == "case1":
                    await cur.execute("UPDATE Lab SET case1 = case1 - %s WHERE lab_id = %s", (amount, user_id))
                elif bet_type == "case2":
                    await cur.execute("UPDATE Lab SET case2 = case2 - %s WHERE lab_id = %s", (amount, user_id))
        
        # Определяем результат
        outcome = roll_outcome(chances)
        mult = outcome["mult"]
        win_amount = int(amount * mult)
        final_emoji = outcome["emoji"]
        
        # Начисляем выигрыш
        if win_amount > 0:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    if bet_type == "resource":
                        await cur.execute("UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s", (win_amount, user_id))
                    elif bet_type == "epicoins":
                        await cur.execute("UPDATE Lab SET epicoins = epicoins + %s WHERE lab_id = %s", (win_amount, user_id))
                    elif bet_type == "case1":
                        await cur.execute("UPDATE Lab SET case1 = case1 + %s WHERE lab_id = %s", (win_amount, user_id))
                    elif bet_type == "case2":
                        await cur.execute("UPDATE Lab SET case2 = case2 + %s WHERE lab_id = %s", (win_amount, user_id))
        
        # Записываем в историю
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO Casino (user_id, bet_type, bet_amount, game, result, win_amount)
                    VALUES (%s, %s, %s, 'roulette', %s, %s)
                """, (user_id, bet_type, amount, outcome["name"], win_amount))
        
        # ===== АНИМАЦИЯ =====
        anim_msg = await msg.reply(
            f"🎰 <b>Крутим барабан...</b>\n\n"
            f"╔═══════════════════╗\n"
            f"║  🎰  🎰  🎰  🎰  🎰  ║\n"
            f"╚═══════════════════╝\n\n"
            f"💰 Ставка: {format_money(amount)} {unit}",
            parse_mode="HTML"
        )
        
        from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

        spin_count = 4
        for i in range(spin_count):
            await asyncio.sleep(0.6)

            e1 = random.choice(SLOT_EMOJIS)
            e2 = random.choice(SLOT_EMOJIS)
            e3 = random.choice(SLOT_EMOJIS)
            e4 = random.choice(SLOT_EMOJIS)
            e5 = random.choice(SLOT_EMOJIS)

            try:
                await anim_msg.edit_text(
                    f"🎰 <b>Крутим барабан...</b>\n\n"
                    f"╔═══════════════════╗\n"
                    f"║  {e1}  {e2}  {e3}  {e4}  {e5}  ║\n"
                    f"╚═══════════════════╝\n\n"
                    f"💰 Ставка: {format_money(amount)} {unit}",
                    parse_mode="HTML"
                )
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except TelegramBadRequest:
                pass
            except Exception:
                pass
        
        # Финальный результат
        if mult == 0:
            result_text = (
                f"🎰 <b>Барабан остановился!</b>\n\n"
                f"╔═══════════════════╗\n"
                f"║  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  ║\n"
                f"╚═══════════════════╝\n\n"
                f"💀 <b>ПРОИГРЫШ</b>\n\n"
                f"🎰 Исход: {outcome['name']}\n"
                f"💰 Ставка: {format_money(amount)} {unit}\n"
                f"💔 Потеряно: <b>-{format_money(amount)}</b> {unit}"
            )
        elif mult < 1:
            result_text = (
                f"🎰 <b>Барабан остановился!</b>\n\n"
                f"╔═══════════════════╗\n"
                f"║  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  ║\n"
                f"╚═══════════════════╝\n\n"
                f"{outcome['emoji']} <b>{outcome['name'].upper()}</b>\n\n"
                f"🎰 Исход: {outcome['name']}\n"
                f"💰 Ставка: {format_money(amount)} {unit}\n"
                f"📉 Возврат: <b>{format_money(win_amount)}</b> {unit}\n"
                f"💔 Потеряно: <b>-{format_money(amount - win_amount)}</b> {unit}"
            )
        elif mult == 1:
            result_text = (
                f"🎰 <b>Барабан остановился!</b>\n\n"
                f"╔═══════════════════╗\n"
                f"║  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  ║\n"
                f"╚═══════════════════╝\n\n"
                f"💰 <b>ВОЗВРАТ</b>\n\n"
                f"🎰 Исход: {outcome['name']}\n"
                f"💰 Ставка: {format_money(amount)} {unit}\n"
                f"↩️ Возвращено: <b>{format_money(win_amount)}</b> {unit}"
            )
        else:
            profit = win_amount - amount
            result_text = (
                f"🎰 <b>Барабан остановился!</b>\n\n"
                f"╔═══════════════════╗\n"
                f"║  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  {final_emoji}  ║\n"
                f"╚═══════════════════╝\n\n"
                f"{outcome['emoji']} <b>{outcome['name'].upper()}!</b>\n\n"
                f"🎰 Исход: {outcome['name']}\n"
                f"💰 Ставка: {format_money(amount)} {unit}\n"
                f"🏆 Выигрыш: <b>+{format_money(profit)}</b> {unit}\n"
                f"💎 Получено: <b>{format_money(win_amount)}</b> {unit}"
            )
        
        await anim_msg.edit_text(
            result_text + "\n\n🎰 Нажмите, чтобы сыграть ещё!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎰 Играть снова", callback_data="casino_again")],
            ])
        )
    
    except ValueError:
        await msg.reply("❌ Введите число!")
        return

    await call.answer("🎰 Готово!")


# ===== ИГРАТЬ СНОВА (шлёт НОВОЕ сообщение) =====
@router.callback_query(F.data == "casino_again")
async def casino_again(call: CallbackQuery, pool: Pool):
    await send_casino_menu(call.message, pool, call.from_user.id, is_callback=False)
    await call.answer("🎰 Новая игра!")

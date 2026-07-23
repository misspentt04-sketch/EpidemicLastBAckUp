import time
import random
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

cases_router = Router()

def get_cases_keyboard():
    kb = [
        [InlineKeyboardButton(text="🛒 Купить Кейс 1", callback_data="buy_case_1")],
        [
            InlineKeyboardButton(text="📦 Открыть Кейс 1", callback_data="open_case_1"),
            InlineKeyboardButton(text="💎 Открыть Кейс 2", callback_data="open_case_2")
        ],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_cases_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== 1. ФАРМ ====================
@cases_router.message(F.text.lower() == "фарм")
@cases_router.message(Command("farm"))
async def cmd_farm(msg: types.Message, db):
    user_id = msg.from_user.id
    
    await db.execute("SELECT epicoins, case1, case2, last_farm FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return

    if isinstance(lab, dict):
        last_farm = lab.get("last_farm", 0) or 0
    else:
        last_farm = lab[3] or 0

    now = int(time.time())
    cooldown = 4 * 3600  # 4 часа

    if now - last_farm < cooldown:
        rem_sec = cooldown - (now - last_farm)
        hours = rem_sec // 3600
        minutes = (rem_sec % 3600) // 60
        await msg.reply(f"⏳ Следующий сбор будет доступен через <b>{hours} ч. {minutes} мин.</b>")
        return

    reward = random.randint(50, 250)
    await db.execute(
        "UPDATE Lab SET epicoins = epicoins + %s, last_farm = %s WHERE lab_id = %s;",
        (reward, now, user_id)
    )
    
    await msg.reply(
        "🧪 Вы успешно провели научный сбор и получили:\n"
        f"<b>+{reward} 🪙 эпикоинов</b>"
    )

# ==================== 2. КЕЙСЫ (ИНВЕНТАРЬ) ====================
@cases_router.message(F.text.lower().in_(["кейс", "кейсы"]))
@cases_router.message(Command("case"))
async def cmd_cases(msg: types.Message, db):
    user_id = msg.from_user.id
    
    await db.execute("SELECT epicoins, case1, case2, last_farm FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return

    if isinstance(lab, dict):
        epicoins = lab.get("epicoins", 0) or 0
        case1 = lab.get("case1", 0) or 0
        case2 = lab.get("case2", 0) or 0
    else:
        epicoins = lab[0] or 0
        case1 = lab[1] or 0
        case2 = lab[2] or 0

    text = (
        "🎒 <b>Инвентарь кейсов:</b>\n\n"
        f"🪙 Баланс: <b>{epicoins} эпикоинов</b>\n\n"
        f"📦 Обычные кейсы (Кейс 1): <b>{case1} шт.</b> (Цена: 500 🪙)\n"
        f"💎 Донат кейсы (Кейс 2): <b>{case2} шт.</b>"
    )
    
    await msg.reply(text, reply_markup=get_cases_keyboard())

# ==================== CALLBACKS ====================
@cases_router.callback_query(F.data == "close_cases_menu")
async def cb_close(call: CallbackQuery):
    await call.message.delete()

@cases_router.callback_query(F.data == "buy_case_1")
async def cb_buy_case1(call: CallbackQuery, db):
    user_id = call.from_user.id
    
    await db.execute("SELECT epicoins, case1, case2 FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    
    if not lab:
        await call.answer("❌ У вас нет лаборатории!", show_alert=True)
        return

    epicoins = (lab.get("epicoins", 0) if isinstance(lab, dict) else lab[0]) or 0

    if epicoins < 500:
        await call.answer("❌ У вас недостаточно эпикоинов (нужно 500 🪙)!", show_alert=True)
        return

    await db.execute(
        "UPDATE Lab SET epicoins = epicoins - 500, case1 = case1 + 1 WHERE lab_id = %s;",
        (user_id,)
    )
    
    await db.execute("SELECT epicoins, case1, case2 FROM Lab WHERE lab_id = %s;", (user_id,))
    updated_lab = await db.fetchone()
    
    if isinstance(updated_lab, dict):
        up_ep = updated_lab.get("epicoins", 0) or 0
        up_c1 = updated_lab.get("case1", 0) or 0
        up_c2 = updated_lab.get("case2", 0) or 0
    else:
        up_ep = updated_lab[0] or 0
        up_c1 = updated_lab[1] or 0
        up_c2 = updated_lab[2] or 0

    text = (
        "🎒 <b>Инвентарь кейсов:</b>\n\n"
        f"🪙 Баланс: <b>{up_ep} эпикоинов</b>\n\n"
        f"📦 Обычные кейсы (Кейс 1): <b>{up_c1} шт.</b> (Цена: 500 🪙)\n"
        f"💎 Донат кейсы (Кейс 2): <b>{up_c2} шт.</b>"
    )
    await call.message.edit_text(text, reply_markup=get_cases_keyboard())
    await call.answer("✅ Вы успешно купили Кейс 1!")

@cases_router.callback_query(F.data == "open_case_1")
async def cb_open_case1(call: CallbackQuery, db):
    user_id = call.from_user.id
    
    await db.execute("SELECT case1 FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    
    if not lab:
        await call.answer("❌ У вас нет лаборатории!", show_alert=True)
        return

    case1 = (lab.get("case1", 0) if isinstance(lab, dict) else lab[0]) or 0

    if case1 < 1:
        await call.answer("❌ У вас нет Кейсов 1!", show_alert=True)
        return

    lvl = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 18, 8, 4])[0]
    item_type = random.choices(
        ['pathogens', 'infect', 'immunity', 'lethality'],
        weights=[35, 15, 25, 25]
    )[0]

    # При выпадении патогена прокачиваем и pathogens, и ready_pathogens одновременно
    if item_type == 'pathogens':
        query = "UPDATE Lab SET case1 = case1 - 1, pathogens = pathogens + %s, ready_pathogens = ready_pathogens + %s WHERE lab_id = %s;"
        reward_text = f"+{lvl} к уровню патогена и +{lvl} готовый патоген"
        params = (lvl, lvl, user_id)
    elif item_type == 'infect':
        query = "UPDATE Lab SET case1 = case1 - 1, infect = infect + %s WHERE lab_id = %s;"
        reward_text = f"+{lvl} зз"
        params = (lvl, user_id)
    elif item_type == 'immunity':
        query = "UPDATE Lab SET case1 = case1 - 1, immunity = immunity + %s WHERE lab_id = %s;"
        reward_text = f"+{lvl} иммуна"
        params = (lvl, user_id)
    elif item_type == 'lethality':
        query = "UPDATE Lab SET case1 = case1 - 1, lethality = lethality + %s WHERE lab_id = %s;"
        reward_text = f"+{lvl} летальности"
        params = (lvl, user_id)

    await db.execute(query, params)
    await call.message.answer(f"🎉 Вы открыли 1 кейс и получили: <b>{reward_text}</b>")
    await call.answer()

@cases_router.callback_query(F.data == "open_case_2")
async def cb_open_case2(call: CallbackQuery, db):
    user_id = call.from_user.id
    
    await db.execute("SELECT case2 FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    
    if not lab:
        await call.answer("❌ У вас нет лаборатории!", show_alert=True)
        return

    case2 = (lab.get("case2", 0) if isinstance(lab, dict) else lab[0]) or 0

    if case2 < 1:
        await call.answer("❌ У вас нет Донат кейсов!", show_alert=True)
        return

    is_super = random.random() < 0.05

    if is_super:
        await db.execute(
            "UPDATE Lab SET case2 = case2 - 1, infect = infect + 5, immunity = immunity + 5 WHERE lab_id = %s;",
            (user_id,)
        )
        reward_text = "🌟 СУПЕРПРИЗ! +5 зз и +5 иммуна"
    else:
        lvl = random.choices([3, 4, 5, 6, 7], weights=[35, 30, 20, 10, 5])[0]
        item_type = random.choice(['infect', 'immunity'])

        if item_type == 'infect':
            await db.execute(
                "UPDATE Lab SET case2 = case2 - 1, infect = infect + %s WHERE lab_id = %s;",
                (lvl, user_id)
            )
            reward_text = f"+{lvl} зз"
        else:
            await db.execute(
                "UPDATE Lab SET case2 = case2 - 1, immunity = immunity + %s WHERE lab_id = %s;",
                (lvl, user_id)
            )
            reward_text = f"+{lvl} иммуна"

    await call.message.answer(f"🎉 Вы открыли 1 донат кейс и получили: <b>{reward_text}</b>")
    await call.answer()

async def admin_give_coins(msg: types.Message, db):
    args = msg.text.split()
    target_id = None
    amount = 0
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        if len(args) >= 3:
            try: amount = int(args[2])
            except ValueError: pass
        elif len(args) == 2:
            try: amount = int(args[1])
            except ValueError: pass
    else:
        if len(args) >= 3:
            try:
                target_id = int(args[2])
                amount = int(args[3])
            except ValueError: pass
    if not target_id or amount <= 0:
        return
    await db.execute("UPDATE Lab SET epicoins = epicoins + %s WHERE lab_id = %s;", (amount, target_id))

async def admin_give_case(msg: types.Message, db):
    args = msg.text.split()
    target_id = None
    case_type = 1
    amount = 1
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        if len(args) >= 3:
            try:
                case_type = int(args[2])
                amount = int(args[3]) if len(args) >= 4 else 1
            except ValueError: pass
        elif len(args) == 2:
            try: amount = int(args[1])
            except ValueError: pass
    else:
        if len(args) >= 4:
            try:
                target_id = int(args[2])
                case_type = int(args[3])
                amount = int(args[4]) if len(args) >= 5 else 1
            except ValueError: pass
    if not target_id or case_type not in (1, 2) or amount <= 0:
        return
    col = "case1" if case_type == 1 else "case2"
    await db.execute(f"UPDATE Lab SET {col} = {col} + %s WHERE lab_id = %s;", (amount, target_id))

# ==================== АДМИН-КОМАНДЫ (ВЫДАЧА) ====================
@cases_router.message(F.text.lower().contains("выдать коины"))
async def admin_give_coins(msg: types.Message, db):
    args = msg.text.split()
    if msg.from_user.id != 7972320837: return
    target_id = None
    amount = 0

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        for arg in args:
            if arg.isdigit():
                amount = int(arg)
                break
    else:
        if len(args) >= 3:
            try:
                target_id = int(args[2])
                amount = int(args[3])
            except ValueError:
                pass

    if not target_id or amount <= 0:
        await msg.reply("❌ Ошибка формата!\nПример реплаем: <code>!выдать коины 500</code>\nПример по ID: <code>!выдать коины 123456789 500</code>")
        return

    await db.execute("UPDATE Lab SET epicoins = epicoins + %s WHERE lab_id = %s;", (amount, target_id))
    await msg.reply(f"✅ Успешно выдано <b>{amount} 🪙</b> пользователю <code>{target_id}</code>!")

@cases_router.message(F.text.lower().contains("выдать кейс"))
async def admin_give_case(msg: types.Message, db):
    if msg.from_user.id != 7972320837: return
    args = msg.text.split()
    target_id = None
    case_type = 1
    amount = 1

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        digits = [int(arg) for arg in args if arg.isdigit()]
        if len(digits) >= 2:
            case_type, amount = digits[0], digits[1]
        elif len(digits) == 1:
            amount = digits[0]
    else:
        digits = [int(arg) for arg in args if arg.isdigit()]
        if len(digits) >= 3:
            target_id, case_type, amount = digits[0], digits[1], digits[2]

    if not target_id or case_type not in (1, 2) or amount <= 0:
        await msg.reply("❌ Ошибка формата!\nПример реплаем: <code>!выдать кейс 1 3</code> (тип, кол-во)\nПример по ID: <code>!выдать кейс 123456789 1 3</code>")
        return

    col = "case1" if case_type == 1 else "case2"
    await db.execute(f"UPDATE Lab SET {col} = {col} + %s WHERE lab_id = %s;", (amount, target_id))
    await msg.reply(f"✅ Успешно выдано <b>{amount} шт. Кейсов {case_type}</b> пользователю <code>{target_id}</code>!")

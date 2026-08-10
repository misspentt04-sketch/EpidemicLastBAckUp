from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import time
import random
from aiogram import Bot, Router, types, F
from aiogram.filters import Command, Command
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

    await db.execute("SELECT case1, science FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()

    if not lab:
        await call.answer("❌ У вас нет лаборатории!", show_alert=True)
        return

    if isinstance(lab, dict):
        case1 = lab.get("case1", 0) or 0
        science = lab.get("science", 0) or 0
    else:
        case1 = lab[0] or 0
        science = lab[1] or 0

    if case1 < 1:
        await call.answer("❌ У вас нет Кейсов 1!", show_alert=True)
        return

    if random.random() < 0.025:
        await db.execute(
            "UPDATE Lab SET case1 = case1 - 1, case2 = case2 + 1 WHERE lab_id = %s;",
            (user_id,)
        )
        reward_text = "💎 1 Донат Кейс!"
    else:
        lvl = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 18, 8, 4])[0]

        if science < 60:
            items = ['pathogens', 'infect', 'immunity', 'lethality', 'science']
            weights = [30, 20, 20, 20, 10]
        else:
            items = ['pathogens', 'infect', 'immunity', 'lethality']
            weights = [40, 20, 20, 20]

        item_type = random.choices(items, weights=weights)[0]

        if item_type == 'pathogens':
            await db.execute(
                "UPDATE Lab SET case1 = case1 - 1, pathogens = pathogens + %s, ready_pathogens = LEAST(ready_pathogens + %s, pathogens + %s) WHERE lab_id = %s;",
                (lvl, lvl, lvl, user_id)
            )
            reward_text = f"+{lvl} к уровню патогена и +{lvl} готовый патоген"
        elif item_type == 'infect':
            await db.execute(
                "UPDATE Lab SET case1 = case1 - 1, infect = infect + %s WHERE lab_id = %s;",
                (lvl, user_id)
            )
            reward_text = f"+{lvl} зз"
        elif item_type == 'immunity':
            await db.execute(
                "UPDATE Lab SET case1 = case1 - 1, immunity = immunity + %s WHERE lab_id = %s;",
                (lvl, user_id)
            )
            reward_text = f"+{lvl} иммуна"
        elif item_type == 'lethality':
            await db.execute(
                "UPDATE Lab SET case1 = case1 - 1, lethality = lethality + %s WHERE lab_id = %s;",
                (lvl, user_id)
            )
            reward_text = f"+{lvl} летальности"
        elif item_type == 'science':
            actual_lvl = min(lvl, 3, 60 - science)
            await db.execute(
                "UPDATE Lab SET case1 = case1 - 1, science = science + %s WHERE lab_id = %s;",
                (actual_lvl, user_id)
            )
            reward_text = f"+{actual_lvl} к разработке"

    ch_sci = "9.75%" if science < 60 else "0%"
    ch_pat = "29.25%" if science < 60 else "39.0%"
    ch_oth = "19.5%" if science < 60 else "19.5%"

    lines = [
        f"📦 Вы открыли <b>1 обычный кейс</b> и получили: <b>{reward_text}</b>",
        "<blockquote expandable>",
        "📊 <b>Шансы на дроп:</b>",
        f"├ 💎 <b>Донат-кейс:</b> <code>2.5%</code>",
        f"├ 🧪 <b>Патогены:</b> <code>{ch_pat}</code>",
        f"├ ☣️ <b>ЗЗ / 🛡 Иммун / ☠️ Летальность:</b> по <code>{ch_oth}</code>",
        f"└ 🧬 <b>Разработка (макс +3):</b> <code>{ch_sci}</code>",
        "</blockquote>"
    ]
    text = chr(10).join(lines)

    await call.message.answer(text)
    await call.answer()

@cases_router.callback_query(F.data == "open_case_2")
async def cb_open_case2(call: CallbackQuery, db):
    user_id = call.from_user.id

    await db.execute("SELECT case2, science FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()

    if not lab:
        await call.answer("❌ У вас нет лаборатории!", show_alert=True)
        return

    if isinstance(lab, dict):
        case2 = lab.get("case2", 0) or 0
        science = lab.get("science", 0) or 0
    else:
        case2 = lab[0] or 0
        science = lab[1] or 0

    if case2 < 1:
        await call.answer("❌ У вас нет Донат кейсов!", show_alert=True)
        return

    roll = random.random()

    if roll < 0.025:
        await db.execute(
            "UPDATE Lab SET case2 = case2 + 1 WHERE lab_id = %s;",
            (user_id,)
        )
        reward_text = "🎰 ДЖЕКПОТ! +2 Донат Кейса"
    elif roll < 0.075:
        await db.execute(
            "UPDATE Lab SET case2 = case2 - 1, infect = infect + 5, immunity = immunity + 5 WHERE lab_id = %s;",
            (user_id,)
        )
        reward_text = "🌟 СУПЕРПРИЗ! +5 зз и +5 иммуна"
    else:
        lvl = random.choices([3, 4, 5, 6, 7], weights=[35, 30, 20, 10, 5])[0]

        items = ['infect', 'immunity']
        if science <= 57:
            items.append('science')

        item_type = random.choice(items)

        if item_type == 'infect':
            await db.execute(
                "UPDATE Lab SET case2 = case2 - 1, infect = infect + %s WHERE lab_id = %s;",
                (lvl, user_id)
            )
            reward_text = f"+{lvl} зз"
        elif item_type == 'immunity':
            await db.execute(
                "UPDATE Lab SET case2 = case2 - 1, immunity = immunity + %s WHERE lab_id = %s;",
                (lvl, user_id)
            )
            reward_text = f"+{lvl} иммуна"
        elif item_type == 'science':
            actual_lvl = min(lvl, 60 - science)
            await db.execute(
                "UPDATE Lab SET case2 = case2 - 1, science = science + %s WHERE lab_id = %s;",
                (actual_lvl, user_id)
            )
            reward_text = f"+{actual_lvl} к разработке"

    ch_normal = "30.8%" if science <= 57 else "46.2%"

    lines = [
        f"💎 Вы открыли <b>1 донат кейс</b> и получили: <b>{reward_text}</b>",
        "<blockquote expandable>",
        "📊 <b>Шансы на дроп:</b>",
        "├ 🎰 <b>ДЖЕКПОТ (+2 ДК):</b> <code>2.5%</code>",
        "├ 🌟 <b>СУПЕРПРИЗ (+5 ЗЗ и +5 Иммун):</b> <code>5.0%</code>",
        f"├ ☣️ <b>ЗЗ:</b> <code>{ch_normal}</code>",
        f"├ 🛡 <b>Иммунитет:</b> <code>{ch_normal}</code>"
    ]
    if science <= 57:
        lines.append(f"├ 🧬 <b>Разработка:</b> <code>{ch_normal}</code>")

    lines.append("└ 🎲 <b>Уровень прибавки:</b> +3 (35%), +4 (30%), +5 (20%), +6 (10%), +7 (5%)")
    lines.append("</blockquote>")
    text = chr(10).join(lines)

    await call.message.answer(text)
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
    if msg.from_user.id not in [7972320837, 7958133684]: return
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
    if msg.from_user.id not in [7972320837, 7958133684]: return
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


# ==================== CRYPTO DONATES ====================
from aiocryptopay import AioCryptoPay, Networks
from core.settings import settings

async def create_crypto_invoice(amount: float, asset: str, description: str, payload: str):
    crypto_sec = getattr(settings, "crypto", None)
    token = getattr(crypto_sec, "token", "616234:AA1jugwJn29SYNbuzSTsL4DW1ytxcP3AhqZ") if crypto_sec else "616234:AA1jugwJn29SYNbuzSTsL4DW1ytxcP3AhqZ"
    crypto = AioCryptoPay(token=token, network=Networks.MAIN_NET)
    invoice = await crypto.create_invoice(
        asset=asset,
        amount=amount,
        description=description,
        payload=payload
    )
    await crypto.close()
    return invoice.bot_invoice_url

@cases_router.callback_query(F.data == "buy_donate_case")
async def process_buy_case_select(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 шт. (1 USDT)", callback_data="buy_case_c_1"),
            InlineKeyboardButton(text="3 шт. (3 USDT)", callback_data="buy_case_c_3"),
            InlineKeyboardButton(text="5 шт. (5 USDT)", callback_data="buy_case_c_5"),
        ],
        [
            InlineKeyboardButton(text="10 шт. (10 USDT)", callback_data="buy_case_c_10"),
            InlineKeyboardButton(text="25 шт. (25 USDT)", callback_data="buy_case_c_25"),
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_crypto_buy")]
    ])
    
    await callback.message.answer(
        "🎁 <b>Покупка Донат-кейсов за Crypto (USDT)</b>\n\n"
        "Выберите количество для покупки (максимум 25 шт.):",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@cases_router.callback_query(F.data == "cancel_crypto_buy")
async def cancel_crypto(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Отменено")

@cases_router.callback_query(F.data.startswith("buy_case_c_"))
async def process_case_count_btn(callback: CallbackQuery):
    count = int(callback.data.split("_")[-1])
    price = float(count)
    
    await callback.answer("⏳ Генерируем счет...")
    try:
        url = await create_crypto_invoice(
            amount=price,
            asset="USDT",
            description=f"Покупка Донат-кейсов ({count} шт.) в Epidemic",
            payload=f"case_{callback.from_user.id}_{count}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 Оплатить {price:.2f} USDT", url=url)]
        ])
        await callback.message.answer(
            f"🎁 <b>Счет на {count} шт. Донат-кейсов готов!</b>\n\n"
            f"<b>К оплате:</b> {price:.2f} USDT\n\n"
            f"Нажмите кнопку ниже для перехода к оплате в CryptoBot:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при создании счета: {e}")

@cases_router.callback_query(F.data == "buy_check_lab")
async def process_buy_check_lab(callback: CallbackQuery):
    await callback.answer("⏳ Генерируем счет...")
    try:
        url = await create_crypto_invoice(
            amount=0.25,
            asset="USDT",
            description="Покупка 1 Просмотра Лаборатории в Epidemic",
            payload=f"lab_{callback.from_user.id}_1"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить 0.25 USDT", url=url)]
        ])
        await callback.message.answer(
            "🔬 <b>Счет на просмотр лаборатории сформирован!</b>\n\n"
            "<b>Количество:</b> 1 шт.\n"
            "<b>К оплате:</b> 0.25 USDT\n\n"
            "Нажмите кнопку ниже для перехода к оплате:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при создании счета: {e}")


@cases_router.message(Command("donate"))
async def cmd_donate_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Купить Донат-кейсы", callback_data="buy_donate_case")],
        [InlineKeyboardButton(text="🔬 Купить Просмотр Лабы (0.25 USDT)", callback_data="buy_check_lab")]
    ])
    await message.answer(
        "💎 <b>Магазин Доната Epidemic</b>\n\n"
        "Выберите интересующий раздел для покупки через CryptoBot:",
        reply_markup=kb,
        parse_mode="HTML"
    )


# ==================== CHECK LAB LOGIC ====================

@cases_router.message(Command("check_lab"))
async def cmd_check_lab(message: Message, repo_biowar):
    user_id = message.from_user.id
    ADMIN_IDS = [7972320837, 7958133684]
    is_admin = user_id in ADMIN_IDS

    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            target_id = int(args[1])

    if not target_id:
        await message.answer("⚠️ <b>Использование:</b>\n• Ответьте командой <code>/check_lab</code> на сообщение игрока\n• Или укажите ID: <code>/check_lab 123456789</code>", parse_mode="HTML")
        return

    if not is_admin:
        res = await repo_biowar.select_one("SELECT lab_checks FROM Users WHERE id=%s;", (user_id,))
        checks_left = res if isinstance(res, int) else 0
        if checks_left <= 0:
            await message.answer("❌ <b>У вас нет доступных просмотров лаборатории!</b>", parse_mode="HTML")
            return
        await repo_biowar.execute_raw("UPDATE Users SET lab_checks = lab_checks - 1 WHERE id=%s;", (user_id,))

    lab_exists = await repo_biowar.select_one("SELECT lab_id FROM Lab WHERE lab_id=%s;", (target_id,))
    if not lab_exists:
        await message.answer("❌ <b>Лаборатория игрока не найдена в базе данных.</b>", parse_mode="HTML")
        return

    p_name = await repo_biowar.select_one("SELECT pathogen_name FROM Lab WHERE lab_id=%s;", (target_id,)) or "Без названия"
    emoji = await repo_biowar.select_one("SELECT customization_emoji FROM Lab WHERE lab_id=%s;", (target_id,)) or "🦠"
    infectivity = await repo_biowar.select_one("SELECT infect FROM Lab WHERE lab_id=%s;", (target_id,)) or 0
    lethality = await repo_biowar.select_one("SELECT lethality FROM Lab WHERE lab_id=%s;", (target_id,)) or 0
    immunity = await repo_biowar.select_one("SELECT immunity FROM Lab WHERE lab_id=%s;", (target_id,)) or 0

    admin_note = " <i>(Админ-доступ)</i>" if is_admin else ""
    text = (
        f"🔬 <b>Лаборатория игрока</b> ID: <code>{target_id}</code>{admin_note}\n\n"
        f"{emoji} <b>Патоген:</b> {p_name}\n"
        f"🎯 <b>Заразность:</b> {infectivity}\n"
        f"☠️ <b>Летальность:</b> {lethality}\n"
        f"🛡 <b>Иммунитет:</b> {immunity}\n"
    )
    await message.answer(text, parse_mode="HTML")


# ==================== ВЫДАЧА ОПЫТА ====================
@cases_router.message(F.text.lower().startswith("выдать опыт") | F.text.lower().startswith("!выдать опыт"))
async def admin_give_exp(msg: types.Message, db):
    if msg.from_user.id not in [7972320837, 7958133684]:
        return

    text_lower = msg.text.lower()
    args = msg.text.split()

    if "всем" in text_lower:
        amount = 0
        for arg in args:
            if arg.isdigit():
                amount = int(arg)
                break
        if amount <= 0:
            err_msg = "❌ Укажите количество опыта!\nПример: <code>!выдать опыт всем 1000</code>"
            await msg.reply(err_msg)
            return

        await db.execute("UPDATE Lab SET bio_experience = bio_experience + %s;", (amount,))
        await msg.reply(f"✅ Успешно выдано по <b>{amount} 🧪 опыта</b> ВСЕМ лабораториям!")
        return

    target_id = None
    amount = 0

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        for arg in args:
            if arg.isdigit():
                amount = int(arg)
                break
    else:
        digits = [int(arg) for arg in args if arg.isdigit()]
        if len(digits) >= 2:
            target_id, amount = digits[0], digits[1]

    if not target_id or amount <= 0:
        fmt_msg = "❌ Ошибка формата!\nРеплаем: <code>!выдать опыт 1000</code>\nПо ID: <code>!выдать опыт 123456789 1000</code>\nВсем: <code>!выдать опыт всем 1000</code>"
        await msg.reply(fmt_msg)
        return

    await db.execute("UPDATE Lab SET bio_experience = bio_experience + %s WHERE lab_id = %s;", (amount, target_id))
    await msg.reply(f"✅ Успешно выдано <b>{amount} 🧪 опыта</b> пользователю <code>{target_id}</code>!")



# ==================== УПРАВЛЕНИЕ ПАТОГЕНАМИ (ТОЛЬКО АДМИНЫ) ====================
@cases_router.message(
    F.text.lower().startswith("!патогены") | 
    F.text.lower().startswith("!-патогены") | 
    F.text.lower().startswith("!+патогены") |
    F.text.lower().startswith("патогены")
)
async def admin_manage_pathogens(msg: types.Message, db):
    if msg.from_user.id not in [7972320837, 7958133684]:
        return

    text_lower = msg.text.lower()
    args = msg.text.split()

    target_id = None
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
    else:
        for arg in args[1:]:
            if arg.isdigit():
                target_id = int(arg)
                break

    if not target_id:
        fmt_msg = "❌ <b>Ошибка!</b> Ответьте на сообщение или укажите ID:\n<code>!патогены сброс 123456789</code>\n<code>!патогены 500 123456789</code>"
        await msg.reply(fmt_msg)
        return

    # РЕЖИМ 1: Сброс до 1к и разработка -999
    if "сброс" in text_lower or text_lower.startswith("!-патогены"):
        await db.execute(
            "UPDATE Lab SET pathogens = 1000, ready_pathogens = 1000, science_time = -999 WHERE lab_id = %s;",
            (target_id,)
        )
        await msg.reply(f"☣️ Патогены игрока <code>{target_id}</code> сброшены до **1 000**, а разработка установлена в **-999**!")
        return

    # РЕЖИМ 2: Выдача / Изменение патогенов на число
    amount = None
    for arg in args:
        cleaned = arg.replace("+", "")
        if cleaned.lstrip("-").isdigit():
            amount = int(cleaned)

    if amount is None:
        await msg.reply("❌ Укажите количество патогенов! Пример: <code>!+патогены 500</code>")
        return

    await db.execute(
        "UPDATE Lab SET pathogens = GREATEST(0, pathogens + %s), ready_pathogens = GREATEST(0, ready_pathogens + %s) WHERE lab_id = %s;",
        (amount, amount, target_id)
    )
    
    action = "выдано" if amount >= 0 else "забрано"
    await msg.reply(f"🧪 Успешно {action} <b>{abs(amount)}</b> патогенов пользователю <code>{target_id}</code>!")

# ==================== УПРАВЛЕНИЕ ПАТОГЕНАМИ ====================
@cases_router.message(
    F.text.lower().startswith("!патогены") | 
    F.text.lower().startswith("!-патогены") | 
    F.text.lower().startswith("!+патогены") |
    F.text.lower().startswith("патогены")
)
async def admin_manage_pathogens(msg: types.Message, db, bot: Bot):
    if msg.from_user.id not in [7972320837, 7958133684]:
        return

    text_lower = msg.text.lower()
    args = msg.text.split()
    admin = msg.from_user

    target_id = None
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
    else:
        for arg in args[1:]:
            if arg.isdigit():
                target_id = int(arg)
                break

    if not target_id:
        fmt_msg = "❌ <b>Ошибка!</b> Ответьте на сообщение или укажите ID:\n<code>!-патогены</code> (реплаем)\n<code>!патогены -500 123456789</code>"
        await msg.reply(fmt_msg)
        return

    # РЕЖИМ 1: Прямая установка отрицательного значения (по умолчанию -999)
    if "сброс" in text_lower or text_lower.startswith("!-патогены") and len(args) == 1:
        await db.execute(
            "UPDATE Lab SET ready_pathogens = -999 WHERE lab_id = %s;",
            (target_id,)
        )
        await msg.reply(f"☣️ Готовые патогены игрока <code>{target_id}</code> установлены в <b>-999</b>!")

        log_txt = f"👑 <b>[Админ-действие]</b>\nАдмин: <a href='tg://user?id={admin.id}'>{admin.full_name}</a> (<code>{admin.id}</code>)\nУстановил ready_pathogens игроку <code>{target_id}</code> в <b>-999</b>."
        try:
            await bot.send_message(-1003688648228, log_txt)
        except Exception as e:
            print(f"[Admin Log Error] {e}")
        return

    # РЕЖИМ 2: Прибавление / отнимание патогенов
    amount = None
    for arg in args:
        cleaned = arg.replace("+", "")
        if cleaned.lstrip("-").isdigit():
            amount = int(cleaned)

    if amount is None:
        await msg.reply("❌ Укажите количество патогенов! Пример: <code>!патогены -500</code>")
        return

    await db.execute(
        "UPDATE Lab SET ready_pathogens = ready_pathogens + %s WHERE lab_id = %s;",
        (amount, target_id)
    )
    
    action = "выдано" if amount >= 0 else "забрано"
    await msg.reply(f"🧪 Успешно {action} <b>{abs(amount)}</b> готовых патогенов пользователю <code>{target_id}</code>!")

    log_txt = f"👑 <b>[Админ-действие]</b>\nАдмин: <a href='tg://user?id={admin.id}'>{admin.full_name}</a> (<code>{admin.id}</code>)\nИзменил ready_pathogens игроку <code>{target_id}</code>: {action} {abs(amount)}."
    try:
        await bot.send_message(-1003688648228, log_txt)
    except Exception as e:
        print(f"[Admin Log Error] {e}")

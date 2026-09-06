from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import time
import random
from aiogram import Bot, Router, types, F
from aiogram.filters import Command, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from core.data.tricks.themes_data import get_theme_text

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
@cases_router.message(F.text.lower().in_(["открыть кейс все", "открыть все кейсы"]))
async def cmd_open_all_cases(msg: types.Message, db):
    """Открывает все кейсы подряд"""
    user_id = msg.from_user.id
    
    await db.execute("SELECT case1, case2, science FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return
    
    if isinstance(lab, dict):
        case1 = lab.get("case1", 0) or 0
        case2 = lab.get("case2", 0) or 0
        science = lab.get("science", 0) or 0
    else:
        case1 = lab[0] or 0
        case2 = lab[1] or 0
        science = lab[2] or 0
    
    total_cases = case1 + case2
    
    if total_cases == 0:
        await msg.reply("❌ У вас нет кейсов!")
        return
    
    # Открываем все кейсы
    opened = 0
    rewards_text = []
    
    # Открываем Case 1
    for _ in range(case1):
        if random.random() < 0.025:
            await db.execute(
                "UPDATE Lab SET case1 = case1 - 1, case2 = case2 + 1 WHERE lab_id = %s;",
                (user_id,)
            )
            rewards_text.append("💎 +1 Донат Кейс")
        else:
            lvl = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 18, 8, 4])[0]
            items = ['pathogens', 'infect', 'immunity', 'lethality', 'science']
            weights = [30, 20, 20, 20, 10]
            item_type = random.choices(items, weights=weights)[0]
            
            if item_type == 'pathogens':
                await db.execute(
                    "UPDATE Lab SET case1 = case1 - 1, pathogens = pathogens + %s, ready_pathogens = LEAST(ready_pathogens + %s, pathogens + %s) WHERE lab_id = %s;",
                    (lvl, lvl, lvl, user_id)
                )
                rewards_text.append(f"+{lvl} к патогенам")
            elif item_type == 'infect':
                await db.execute(
                    "UPDATE Lab SET case1 = case1 - 1, infect = infect + %s WHERE lab_id = %s;",
                    (lvl, user_id)
                )
                rewards_text.append(f"+{lvl} зз")
            elif item_type == 'immunity':
                await db.execute(
                    "UPDATE Lab SET case1 = case1 - 1, immunity = immunity + %s WHERE lab_id = %s;",
                    (lvl, user_id)
                )
                rewards_text.append(f"+{lvl} иммуна")
            elif item_type == 'lethality':
                await db.execute(
                    "UPDATE Lab SET case1 = case1 - 1, lethality = lethality + %s WHERE lab_id = %s;",
                    (lvl, user_id)
                )
                rewards_text.append(f"+{lvl} летальности")
            elif item_type == 'science':
                actual_lvl = min(lvl, 60 - science)
                await db.execute(
                    "UPDATE Lab SET case1 = case1 - 1, science = science + %s WHERE lab_id = %s;",
                    (actual_lvl, user_id)
                )
                science += actual_lvl
                rewards_text.append(f"+{actual_lvl} к разработке")
        opened += 1
    
    # Открываем Case 2
    for _ in range(case2):
        roll = random.random()
        
        if roll < 0.025:
            await db.execute(
                "UPDATE Lab SET case2 = case2 + 1 WHERE lab_id = %s;",
                (user_id,)
            )
            rewards_text.append("🎰 ДЖЕКПОТ! +2 Донат Кейса")
        elif roll < 0.075:
            await db.execute(
                "UPDATE Lab SET case2 = case2 - 1, infect = infect + 5, immunity = immunity + 5 WHERE lab_id = %s;",
                (user_id,)
            )
            rewards_text.append("🌟 +5 зз и +5 иммуна")
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
                rewards_text.append(f"+{lvl} зз")
            elif item_type == 'immunity':
                await db.execute(
                    "UPDATE Lab SET case2 = case2 - 1, immunity = immunity + %s WHERE lab_id = %s;",
                    (lvl, user_id)
                )
                rewards_text.append(f"+{lvl} иммуна")
            elif item_type == 'science':
                actual_lvl = min(lvl, 60 - science)
                await db.execute(
                    "UPDATE Lab SET case2 = case2 - 1, science = science + %s WHERE lab_id = %s;",
                    (actual_lvl, user_id)
                )
                science += actual_lvl
                rewards_text.append(f"+{actual_lvl} к разработке")
        opened += 1
    
    # Суммируем награды
    total_rewards = {}
    for reward in rewards_text:
        # Парсим "+N к item"
        import re
        match = re.search(r'\+(\d+) к (\w+)', reward)
        if match:
            amount = int(match.group(1))
            item = match.group(2)
            total_rewards[item] = total_rewards.get(item, 0) + amount
    
    # Формируем итог
    result = f"🎁 <b>Открыто {opened} кейсов:</b>\n\n"
    for item, amount in total_rewards.items():
        result += f"+{amount} к {item}\n"
    
    await msg.reply(result, parse_mode="HTML")

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

    # Используем тему для текста кейсов
    cases_text = await get_theme_text(db, user_id, "cases_menu")
    text = cases_text.format(
        epicoins=f"{epicoins:,}",
        case1=case1,
        case2=case2
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

    cases_text = await get_theme_text(db, user_id, "cases_menu")
    text = cases_text.format(
        epicoins=f"{up_ep:,}",
        case1=up_c1,
        case2=up_c2
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
        f"├ 🧪 <b>🧪 Готовых патогенов:</b> <code>{ch_pat}</code>",
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




# ==================== CHECK LAB LOGIC ====================

@cases_router.message(Command("check_lab"))
async def cmd_check_lab(message: Message, repo_biowar):
    user_id = message.from_user.id
    ADMIN_IDS = [7972320837, 7958133684, 8236324289]
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
        f"{emoji} <b>🏷 Имя патогена:</b> {p_name}\n"
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


# ==================== АВТОВЫДАЧА ДОНАТ КЕЙСОВ ====================

def calculate_cases_bonus(count: int) -> int:
    return 3 if count >= 10 else (1 if count >= 5 else 0)

async def auto_issue_donate_cases(db_session, user_id: int, cases_count: int, case_type: str = "donate_cases"):
    bonus = calculate_cases_bonus(cases_count)
    total_to_give = cases_count + bonus

    column_map = {
        "donate_cases": "case2",
        "donate": "case2",
        "case1": "case1",
        "1": "case1",
        "case2": "case2",
        "2": "case2",
    }
    col_name = column_map.get(str(case_type).lower(), "case2")

    query = f"UPDATE Lab SET {col_name} = {col_name} + %s WHERE lab_id = %s;"
    await db_session.execute(query, (total_to_give, user_id))

    return total_to_give, bonus


@cases_router.callback_query(F.data.startswith("check_donate_payment:"))
async def process_payment_callback(callback: types.CallbackQuery, state, db):
    user_id = callback.from_user.id
    data = await state.get_data()

    cases_count = data.get("cases_count", 1)
    case_type = data.get("case_type", "donate_cases")

    is_paid = True  # Здесь подключается логика проверки платежа

    if is_paid:
        total_given, bonus = await auto_issue_donate_cases(
            db_session=db,
            user_id=user_id,
            cases_count=cases_count,
            case_type=case_type,
        )

        text = (
            f"✅ <b>Оплата прошла успешно!</b>\n\n"
            f"🎁 Вам автоматически зачислено кейсов: <b>{total_given} шт.</b>"
        )
        if bonus > 0:
            text += f" <i>(из них бонус: +{bonus})</i>"

        await callback.message.edit_text(text, parse_mode="HTML")
        await state.clear()
    else:
        await callback.answer(
            "❌ Оплата еще не поступила. Попробуйте через пару минут.",
            show_alert=True,
        )

# ==================== НОВАЯ КОМАНДА: ЗАБРАТЬ КЕЙС ====================
@cases_router.message(F.text.lower().contains("забрать кейс"))
async def admin_take_case(msg: types.Message, db):
    if msg.from_user.id not in [7972320837, 7958133684, 1758346431]: return
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
        await msg.reply("❌ Ошибка формата!\nПример реплаем: <code>!забрать кейс 1 3</code>\nПример по ID: <code>!забрать кейс 123456789 1 3</code>")
        return
    col = "case1" if case_type == 1 else "case2"
    result = await db.execute(f"SELECT {col} FROM Lab WHERE lab_id = %s;", (target_id,))
    lab = await db.fetchone()
    if not lab:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден в базе!")
        return
    current_cases = lab[0] if isinstance(lab, (tuple, list)) else lab.get(col, 0) or 0
    if current_cases < amount:
        await msg.reply(f"❌ У пользователя <code>{target_id}</code> недостаточно кейсов!\nДоступно: <b>{current_cases}</b> шт. Кейсов {case_type}\nЗапрошено: <b>{amount}</b> шт.")
        return
    await db.execute(f"UPDATE Lab SET {col} = {col} - %s WHERE lab_id = %s;", (amount, target_id))
    await db.execute(f"UPDATE Lab SET {col} = GREATEST(0, {col}) WHERE lab_id = %s;", (target_id,))
    await msg.reply(f"✅ Успешно <b>забрано {amount} шт.</b> Кейсов {case_type}\n👤 Пользователь: <code>{target_id}</code>")


# ==================== НОВАЯ КОМАНДА: ПЕРЕНЕСТИ КЕЙСЫ (СВОП) ====================
@cases_router.message(F.text.lower().contains("перенести кейсы"))
async def admin_transfer_cases(msg: types.Message, db):
    if msg.from_user.id not in [7972320837, 7958133684, 1758346431, 6129560117]: return
    args = msg.text.split()
    if len(args) < 3:
        await msg.reply("❌ Ошибка формата!\nПример: <code>!перенести кейсы 123456789 987654321</code>")
        return
    digits = [int(arg) for arg in args if arg.isdigit()]
    if len(digits) < 2:
        await msg.reply("❌ Ошибка формата!\nНужно указать два ID: <code>!перенести кейсы 123456789 987654321</code>")
        return
    id1, id2 = digits[0], digits[1]
    if id1 == id2:
        await msg.reply("❌ Нельзя переносить кейсы самому себе!")
        return
    
    # Проверяем существование обоих пользователей
    user1 = await db.execute("SELECT lab_id FROM Lab WHERE lab_id = %s;", (id1,))
    user1_exists = await db.fetchone()
    user2 = await db.execute("SELECT lab_id FROM Lab WHERE lab_id = %s;", (id2,))
    user2_exists = await db.fetchone()
    
    if not user1_exists:
        await msg.reply(f"❌ Пользователь <code>{id1}</code> не найден в базе!")
        return
    if not user2_exists:
        await msg.reply(f"❌ Пользователь <code>{id2}</code> не найден в базе!")
        return
    
    # Получаем текущие кейсы у обоих пользователей
    data1 = await db.execute("SELECT case1, case2 FROM Lab WHERE lab_id = %s;", (id1,))
    row1 = await db.fetchone()
    data2 = await db.execute("SELECT case1, case2 FROM Lab WHERE lab_id = %s;", (id2,))
    row2 = await db.fetchone()
    
    if isinstance(row1, dict):
        id1_case1 = row1.get("case1", 0) or 0
        id1_case2 = row1.get("case2", 0) or 0
    else:
        id1_case1 = row1[0] if row1 else 0
        id1_case2 = row1[1] if row1 else 0
    
    if isinstance(row2, dict):
        id2_case1 = row2.get("case1", 0) or 0
        id2_case2 = row2.get("case2", 0) or 0
    else:
        id2_case1 = row2[0] if row2 else 0
        id2_case2 = row2[1] if row2 else 0
    
    # МЕНЯЕМ МЕСТАМИ (своп)
    # Устанавливаем id1 кейсы id2
    await db.execute("UPDATE Lab SET case1 = %s, case2 = %s WHERE lab_id = %s;", (id2_case1, id2_case2, id1))
    # Устанавливаем id2 кейсы id1
    await db.execute("UPDATE Lab SET case1 = %s, case2 = %s WHERE lab_id = %s;", (id1_case1, id1_case2, id2))
    
    total1 = id1_case1 + id1_case2
    total2 = id2_case1 + id2_case2
    
    await msg.reply(
        f"🔄 <b>Кейсы успешно перенесены (своп)!</b>\n\n"
        f"📤 <code>{id1}</code> → <code>{id2}</code>\n"
        f"  • Кейс 1: <b>{id1_case1}</b> шт.\n"
        f"  • Кейс 2: <b>{id1_case2}</b> шт.\n"
        f"  • Всего: <b>{total1}</b> шт.\n\n"
        f"📤 <code>{id2}</code> → <code>{id1}</code>\n"
        f"  • Кейс 1: <b>{id2_case1}</b> шт.\n"
        f"  • Кейс 2: <b>{id2_case2}</b> шт.\n"
        f"  • Всего: <b>{total2}</b> шт."
    )

# ==================== ФУНКЦИЯ ДЛЯ ЛОГИРОВАНИЯ ====================
async def log_admin_action(bot: Bot, admin_id: int, admin_name: str, action: str, target: str, details: str = ""):
    """Отправляет лог админского действия в чат -1003688648228"""
    try:
        log_text = (
            f"👑 <b>[ADMIN ACTION]</b>\n"
            f"👤 Админ: <a href='tg://user?id={admin_id}'>{admin_name}</a> (<code>{admin_id}</code>)\n"
            f"📋 Действие: {action}\n"
            f"🎯 Цель: {target}\n"
            f"📝 Детали: {details}"
        )
        await bot.send_message(-1003688648228, log_text, parse_mode="HTML")
    except Exception as e:
        print(f"[Admin Log Error] {e}")

# ==================== ОБНОВЛЕННАЯ КОМАНДА: ВЫДАТЬ КЕЙС (С ЛОГАМИ) ====================
    if msg.from_user.id not in [7972320837, 7958133684, 1758346431]: return
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
    
    admin_name = msg.from_user.full_name or msg.from_user.username or "Unknown"
    await log_admin_action(bot, msg.from_user.id, admin_name, f"✅ Выдача кейсов (тип {case_type})", f"<code>{target_id}</code>", f"Количество: {amount} шт.")

# ==================== ОБНОВЛЕННАЯ КОМАНДА: ЗАБРАТЬ КЕЙС (С ЛОГАМИ) ====================
@cases_router.message(F.text.lower().contains("забрать кейс"))
async def admin_take_case(msg: types.Message, db, bot: Bot):
    if msg.from_user.id not in [7972320837, 7958133684, 1758346431]: return
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
        await msg.reply("❌ Ошибка формата!\nПример реплаем: <code>!забрать кейс 1 3</code>\nПример по ID: <code>!забрать кейс 123456789 1 3</code>")
        return
    col = "case1" if case_type == 1 else "case2"
    result = await db.execute(f"SELECT {col} FROM Lab WHERE lab_id = %s;", (target_id,))
    lab = await db.fetchone()
    if not lab:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден в базе!")
        return
    current_cases = lab[0] if isinstance(lab, (tuple, list)) else lab.get(col, 0) or 0
    if current_cases < amount:
        await msg.reply(f"❌ У пользователя <code>{target_id}</code> недостаточно кейсов!\nДоступно: <b>{current_cases}</b> шт. Кейсов {case_type}\nЗапрошено: <b>{amount}</b> шт.")
        return
    await db.execute(f"UPDATE Lab SET {col} = {col} - %s WHERE lab_id = %s;", (amount, target_id))
    await db.execute(f"UPDATE Lab SET {col} = GREATEST(0, {col}) WHERE lab_id = %s;", (target_id,))
    await msg.reply(f"✅ Успешно <b>забрано {amount} шт.</b> Кейсов {case_type}\n👤 Пользователь: <code>{target_id}</code>")
    
    admin_name = msg.from_user.full_name or msg.from_user.username or "Unknown"
    await log_admin_action(bot, msg.from_user.id, admin_name, f"❌ Изъятие кейсов (тип {case_type})", f"<code>{target_id}</code>", f"Количество: {amount} шт. (было: {current_cases}, стало: {current_cases - amount})")

# ==================== ОБНОВЛЕННАЯ КОМАНДА: ПЕРЕНЕСТИ КЕЙСЫ (СВОП) (С ЛОГАМИ) ====================
@cases_router.message(F.text.lower().contains("перенести кейсы"))
async def admin_transfer_cases(msg: types.Message, db, bot: Bot):
    if msg.from_user.id not in [7972320837, 7958133684, 1758346431, 6129560117]: return
    args = msg.text.split()
    if len(args) < 3:
        await msg.reply("❌ Ошибка формата!\nПример: <code>!перенести кейсы 123456789 987654321</code>")
        return
    digits = [int(arg) for arg in args if arg.isdigit()]
    if len(digits) < 2:
        await msg.reply("❌ Ошибка формата!\nНужно указать два ID: <code>!перенести кейсы 123456789 987654321</code>")
        return
    id1, id2 = digits[0], digits[1]
    if id1 == id2:
        await msg.reply("❌ Нельзя переносить кейсы самому себе!")
        return

    user1 = await db.execute("SELECT lab_id FROM Lab WHERE lab_id = %s;", (id1,))
    user1_exists = await db.fetchone()
    user2 = await db.execute("SELECT lab_id FROM Lab WHERE lab_id = %s;", (id2,))
    user2_exists = await db.fetchone()

    if not user1_exists:
        await msg.reply(f"❌ Пользователь <code>{id1}</code> не найден в базе!")
        return
    if not user2_exists:
        await msg.reply(f"❌ Пользователь <code>{id2}</code> не найден в базе!")
        return

    data1 = await db.execute("SELECT case1, case2 FROM Lab WHERE lab_id = %s;", (id1,))
    row1 = await db.fetchone()
    data2 = await db.execute("SELECT case1, case2 FROM Lab WHERE lab_id = %s;", (id2,))
    row2 = await db.fetchone()

    if isinstance(row1, dict):
        id1_case1 = row1.get("case1", 0) or 0
        id1_case2 = row1.get("case2", 0) or 0
    else:
        id1_case1 = row1[0] if row1 else 0
        id1_case2 = row1[1] if row1 else 0

    if isinstance(row2, dict):
        id2_case1 = row2.get("case1", 0) or 0
        id2_case2 = row2.get("case2", 0) or 0
    else:
        id2_case1 = row2[0] if row2 else 0
        id2_case2 = row2[1] if row2 else 0

    await db.execute("UPDATE Lab SET case1 = %s, case2 = %s WHERE lab_id = %s;", (id2_case1, id2_case2, id1))
    await db.execute("UPDATE Lab SET case1 = %s, case2 = %s WHERE lab_id = %s;", (id1_case1, id1_case2, id2))

    total1 = id1_case1 + id1_case2
    total2 = id2_case1 + id2_case2

    await msg.reply(
        f"🔄 <b>Кейсы успешно перенесены (своп)!</b>\n\n"
        f"📤 <code>{id1}</code> → <code>{id2}</code>\n"
        f"  • Кейс 1: <b>{id1_case1}</b> шт.\n"
        f"  • Кейс 2: <b>{id1_case2}</b> шт.\n"
        f"  • Всего: <b>{total1}</b> шт.\n\n"
        f"📤 <code>{id2}</code> → <code>{id1}</code>\n"
        f"  • Кейс 1: <b>{id2_case1}</b> шт.\n"
        f"  • Кейс 2: <b>{id2_case2}</b> шт.\n"
        f"  • Всего: <b>{total2}</b> шт."
    )
    
    admin_name = msg.from_user.full_name or msg.from_user.username or "Unknown"
    await log_admin_action(bot, msg.from_user.id, admin_name, f"🔄 Обмен кейсами (своп)", f"<code>{id1}</code> ↔ <code>{id2}</code>", f"ID1: Кейс1={id1_case1}, Кейс2={id1_case2} (всего {total1}) | ID2: Кейс1={id2_case1}, Кейс2={id2_case2} (всего {total2})")

# ==================== ОБНОВЛЕННАЯ КОМАНДА: ВЫДАТЬ КОИНЫ (С ЛОГАМИ) ====================
@cases_router.message(F.text.lower().contains("выдать коины"))
async def admin_give_coins(msg: types.Message, db, bot: Bot):
    args = msg.text.split()
    if msg.from_user.id not in [7972320837, 7958133684, 1758346431]: return
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
    
    admin_name = msg.from_user.full_name or msg.from_user.username or "Unknown"
    await log_admin_action(bot, msg.from_user.id, admin_name, f"💰 Выдача эпикоинов", f"<code>{target_id}</code>", f"Количество: {amount} 🪙")

# ==================== ОБНОВЛЕННАЯ КОМАНДА: ВЫДАТЬ КЕЙС (С ЛОГАМИ) ====================
@cases_router.message(F.text.lower().contains("выдать кейс"))
async def admin_give_case(msg: types.Message, db, bot: Bot):
    if msg.from_user.id not in [7972320837, 7958133684, 1758346431]: return
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
    
    admin_name = msg.from_user.full_name or msg.from_user.username or "Unknown"
    await log_admin_action(bot, msg.from_user.id, admin_name, f"✅ Выдача кейсов (тип {case_type})", f"<code>{target_id}</code>", f"Количество: {amount} шт.")

# ==================== ВЫДАТЬ PTS (АДМИН-КОМАНДА) ====================
@cases_router.message(F.text.lower().contains("выдать птс"))
async def admin_give_pts(msg: types.Message, db):
    if msg.from_user.id not in [7972320837]: return
    args = msg.text.split()
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
        await msg.reply("❌ Ошибка формата!\nПример реплаем: <code>!выдать птс 50</code>\nПример по ID: <code>!выдать птс 123456789 50</code>")
        return

    await db.execute("UPDATE Lab SET pts = pts + %s WHERE lab_id = %s;", (amount, target_id))
    await msg.reply(f"✅ Успешно выдано <b>{amount} PTS</b> пользователю <code>{target_id}</code>!")
    
    # Логируем в чат админов
    try:
        from core.handlers.biowar.donates.cases import log_admin_action
        admin_name = msg.from_user.full_name or msg.from_user.username or "Unknown"
        await log_admin_action(
            msg.bot,
            msg.from_user.id,
            admin_name,
            f"💰 Выдача PTS",
            target_id,
            f"Количество: {amount} PTS"
        )
    except:
        pass

# ==================== ПЕРЕДАТЬ КЕЙС (ОБМЕН МЕЖДУ ИГРОКАМИ) ====================
@cases_router.message(F.text.lower().contains("передать кейс"))
async def cmd_transfer_case(msg: types.Message, db):
    user_id = msg.from_user.id
    args = msg.text.split()
    
    # Проверяем формат: передать кейс @username 1 5 (тип, кол-во)
    if len(args) < 4:
        await msg.reply("❌ Формат: <code>передать кейс @username 1 5</code>\nГде 1 - тип кейса (1 или 2), 5 - количество")
        return
    
    target_username = args[2].replace('@', '')
    try:
        case_type = int(args[3])
        amount = int(args[4]) if len(args) > 4 else 1
    except ValueError:
        await msg.reply("❌ Укажите тип и количество цифрами!\nПример: <code>передать кейс @username 1 5</code>")
        return
    
    if case_type not in (1, 2):
        await msg.reply("❌ Тип кейса: 1 - обычный, 2 - донат")
        return
    
    if amount <= 0:
        await msg.reply("❌ Количество должно быть больше 0")
        return
    
    # Получаем ID получателя по username
    target_id = None
    try:
        # Ищем пользователя по username
        result = await db.execute("SELECT lab_id FROM Lab WHERE lab_id IN (SELECT id FROM Users WHERE username = %s);", (target_username,))
        target_data = await db.fetchone()
        if target_data:
            target_id = target_data[0] if isinstance(target_data, (tuple, list)) else target_data.get('lab_id')
    except:
        pass
    
    if not target_id:
        await msg.reply(f"❌ Пользователь @{target_username} не найден в базе!")
        return
    
    if target_id == user_id:
        await msg.reply("❌ Нельзя передать кейсы самому себе!")
        return
    
    # Проверяем наличие кейсов у отправителя
    col = "case1" if case_type == 1 else "case2"
    result = await db.execute(f"SELECT {col} FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return
    
    current_cases = lab[0] if isinstance(lab, (tuple, list)) else lab.get(col, 0) or 0
    
    if current_cases < amount:
        await msg.reply(f"❌ У вас недостаточно кейсов! Доступно: {current_cases} шт.")
        return
    
    # Передаём кейсы
    await db.execute(f"UPDATE Lab SET {col} = {col} - %s WHERE lab_id = %s;", (amount, user_id))
    await db.execute(f"UPDATE Lab SET {col} = {col} + %s WHERE lab_id = %s;", (amount, target_id))
    
    await msg.reply(
        f"✅ Передано <b>{amount} шт.</b> Кейсов {case_type}\n"
        f"📤 От: <code>{user_id}</code>\n"
        f"📥 Кому: <code>{target_id}</code> (@{target_username})"
    )
    
    # Логируем
    try:
        admin_name = msg.from_user.full_name or msg.from_user.username or "Unknown"
        await log_admin_action(
            msg.bot,
            msg.from_user.id,
            admin_name,
            f"🔄 Передача кейсов (тип {case_type})",
            target_id,
            f"Количество: {amount} шт. от {user_id}"
        )
    except:
        pass

        return

    # Получаем текущий уровень
    result = await db.execute("SELECT rebirth_level FROM Lab WHERE lab_id = %s;", (target_id,))
    lab = await db.fetchone()
    
    if not lab:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден в базе!")
        return

    current_level = lab[0] if isinstance(lab, (tuple, list)) else lab.get('rebirth_level', 0) or 0
    new_level = current_level + level

    await db.execute("UPDATE Lab SET rebirth_level = %s WHERE lab_id = %s;", (new_level, target_id))
    await msg.reply(f"✅ Уровень Rebirth для <code>{target_id}</code> повышен на <b>{level}</b>!\n📊 Было: <b>{current_level}</b> → Стало: <b>{new_level}</b>")

# ==================== ДОБАВИТЬ УРОВЕНЬ REBIRTH (АДМИН) ====================
@cases_router.message(F.text.lower().contains("+рб"))
@cases_router.message(Command("add_rb"))
async def admin_add_rebirth(msg: types.Message, db):
    if msg.from_user.id not in [7972320837]:
        return

    args = msg.text.split()
    target_id = None
    level = 1

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        if len(args) >= 2:
            try:
                level = int(args[1])
            except ValueError:
                pass
    else:
        if len(args) >= 3:
            try:
                target_id = int(args[2])
                level = int(args[3])
            except ValueError:
                pass

    if not target_id or level <= 0:
        await msg.reply("❌ Ошибка формата!\nПример реплаем: <code>+рб 5</code>\nПример по ID: <code>+рб 123456789 5</code>")
        return

    # Получаем текущий уровень
    result = await db.execute("SELECT rebirth_level, bio_experience, bio_resource FROM Lab WHERE lab_id = %s;", (target_id,))
    lab = await db.fetchone()
    
    if not lab:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден в базе!")
        return

    current_level = lab[0] if isinstance(lab, (tuple, list)) else lab.get('rebirth_level', 0) or 0
    new_level = current_level + level

    # Обновляем только rebirth_level, НЕ трогаем опыт и ресурсы
    await db.execute("UPDATE Lab SET rebirth_level = %s WHERE lab_id = %s;", (new_level, target_id))
    
    await msg.reply(
        f"✅ Уровень Rebirth для <code>{target_id}</code> повышен!\n"
        f"📊 Было: <b>{current_level}</b> → Стало: <b>{new_level}</b>\n"
        f"➕ Добавлено: <b>{level}</b> уровней"
    )

# ==================== ЗАБРАТЬ УРОВЕНЬ REBIRTH (АДМИН) ====================
@cases_router.message(F.text.lower().contains("-рб"))
async def admin_remove_rebirth(msg: types.Message, db):
    if msg.from_user.id not in [7972320837]:
        return

    args = msg.text.split()
    target_id = None
    level = 1

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        if len(args) >= 2:
            try:
                level = int(args[1])
            except ValueError:
                pass
    else:
        if len(args) >= 3:
            try:
                target_id = int(args[2])
                level = int(args[3])
            except ValueError:
                pass

    if not target_id or level <= 0:
        await msg.reply("❌ Ошибка формата!\nПример реплаем: <code>-рб 5</code>\nПример по ID: <code>-рб 123456789 5</code>")
        return

    # Получаем текущий уровень
    result = await db.execute("SELECT rebirth_level FROM Lab WHERE lab_id = %s;", (target_id,))
    lab = await db.fetchone()
    
    if not lab:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден в базе!")
        return

    current_level = lab[0] if isinstance(lab, (tuple, list)) else lab.get('rebirth_level', 0) or 0
    
    if current_level <= 0:
        await msg.reply(f"❌ У пользователя <code>{target_id}</code> нет уровней Rebirth!")
        return

    new_level = max(0, current_level - level)
    removed = current_level - new_level

    await db.execute("UPDATE Lab SET rebirth_level = %s WHERE lab_id = %s;", (new_level, target_id))
    
    await msg.reply(
        f"✅ Уровень Rebirth для <code>{target_id}</code> понижен!\n"
        f"📊 Было: <b>{current_level}</b> → Стало: <b>{new_level}</b>\n"
        f"➖ Забрано: <b>{removed}</b> уровней"
    )

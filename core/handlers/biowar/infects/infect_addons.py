async def calculate_vaccine_bio_price(user_id: int, lab_info: dict, fev_seconds: float, repo_biowar) -> tuple[int, str]:
    lethality = await get_effective_lethality(user_id, lab_info, repo_biowar)
    fever_price = int(lab_info.get("immunity", 1) * 15)
    fever_price = 1 if fever_price <= 0 else fever_price

    pet = await repo_biowar.get_my_pet(user_id)
    pet_effect = ""
    if pet and pet.get("current_pet", "").lower() == "мимин":
        fever_price_base = fever_price
        element_pet_emoji = tricks_biowar["pet"]["pets_info"][pet["current_pet"].lower()]["element_emoji"]
        fever_price = max(1, int(fever_price * 0.75))
        discount = fever_price_base - fever_price
        if discount > 0:
            pet_name = pet["current_pet"].title()
            disc_str = intcomma(discount)
            pet_effect = f"\n<b>{element_pet_emoji} {pet_name}</b> снизил расходы вакцины на <b>{disc_str}</b> био-ресурсов"

    return fever_price, pet_effect

async def get_effective_lethality(user_id: int, lab_info: dict, repo_biowar) -> int:
    infecter_row = await repo_biowar.select_one("SELECT victims_owner_id FROM Victims WHERE victim_id = %s;", (user_id,))
    if infecter_row:
        infecter_id = infecter_row.get("victims_owner_id") if isinstance(infecter_row, dict) else (infecter_row[0] if isinstance(infecter_row, (tuple, list)) else infecter_row)
        infecter_lab = await repo_biowar.get_info_user_lab(infecter_id)
        if infecter_lab:
            return max(1, int(infecter_lab.get("lethality", 1)))
    return max(1, int(lab_info.get("lethality", 1)))

import math
from asyncmy.cursors import Cursor
from redis.asyncio import Redis
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot

from humanize import intcomma
from datetime import datetime, timezone

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core import func

from core.data.tricks.tricks_biowar import tricks_biowar

import random


async def vaccine_choice_menu(msg: Message, bot: Bot, redis: Redis):
    user_id = msg.from_user.id
    current_mode = await redis.get(f"vac_pay_mode:{user_id}")
    current_mode = current_mode.decode() if isinstance(current_mode, bytes) else (current_mode or "default")

    mode_text = {
        "bio": "🧬 Био-ресурсы",
        "epi": "🪙 Эпикоины",
        "default": "❓ Каждый раз спрашивать (по умолчанию)"
    }.get(current_mode, "❓ Каждый раз спрашивать")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧬 Био-ресурсы", callback_data=f"set_vac_mode:bio:{user_id}"),
                InlineKeyboardButton(text="🪙 Эпикоины", callback_data=f"set_vac_mode:epi:{user_id}")
            ],
            [
                InlineKeyboardButton(text="🔄 Сбросить (Спрашивать)", callback_data=f"set_vac_mode:default:{user_id}")
            ]
        ]
    )

    text = (
        "⚙️ <b>Настройка автопокупки вакцины</b>\n\n"
        f"Текущий режим: <b>{mode_text}</b>\n\n"
        "Выберите желаемый способ оплаты по умолчанию для команды <code>!купить вакцину</code>:"
    )
    await msg.answer(text, reply_markup=keyboard)


async def cb_set_vac_mode(call: CallbackQuery, redis: Redis):
    user_id = call.from_user.id
    parts = call.data.split(":")
    mode = parts[1]
    target_id = int(parts[2])

    if user_id != target_id:
        return await call.answer("❌ Это не ваше меню!", show_alert=True)

    if mode == "default":
        await redis.delete(f"vac_pay_mode:{user_id}")
        msg_text = "🔄 Режим сброшен. Теперь при покупке вакцины будет появляться выбор."
    elif mode == "bio":
        await redis.set(f"vac_pay_mode:{user_id}", "bio")
        msg_text = "✅ Установлена автоматическая покупка вакцины за 🧬 Био-ресурсы!"
    elif mode == "epi":
        await redis.set(f"vac_pay_mode:{user_id}", "epi")
        msg_text = "✅ Установлена автоматическая покупка вакцины за 🪙 Эпикоины!"

    await call.message.edit_text(msg_text)
    await call.answer("✅ Настройки сохранены!")


async def buy_vaccine(msg: Message, bot: Bot, db: Cursor, redis: Redis, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    pay_mode = await redis.get(f"vac_pay_mode:{user_id}")
    pay_mode = pay_mode.decode() if isinstance(pay_mode, bytes) else pay_mode

    lab_info = await repo_biowar.get_info_user_lab(user_id)

    if not lab_info or not lab_info.get("fever"):
        return await msg.answer(tricks_biowar["infect"]["have_not_fever"])

    fev_seconds = (datetime.fromtimestamp(lab_info["fever"], tz=timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    fev_seconds = 1 if fev_seconds <= 0 else fev_seconds

    # Если установлен автоматический режим оплаты
    if pay_mode == "bio":
        pet = await repo_biowar.get_my_pet(user_id)
        pet_effect = ""
        lethality = await get_effective_lethality(user_id, lab_info, repo_biowar)
        fever_price = int(lab_info.get("immunity", 1) * 15)
        fever_price = 1 if fever_price <= 0 else fever_price

        if pet and pet.get("current_pet", "").lower() == "мимин":
            fever_price_base = fever_price
            element_pet_emoji = tricks_biowar["pet"]["pets_info"][pet["current_pet"].lower()]["element_emoji"]
            fever_price = max(1, int(fever_price * 0.75))
            discount = fever_price_base - fever_price
            if discount > 0:
                pet_name = pet["current_pet"].title()
                disc_str = intcomma(discount)
                pet_effect = f"\n<b>{element_pet_emoji} {pet_name}</b> снизил расходы вакцины на <b>{disc_str}</b> био-ресурсов"

        if lab_info.get("bio_resource", 0) < fever_price:
            return await msg.answer(f"❌ Недостаточно био-ресурсов! Нужно <b>{intcomma(fever_price)}</b> 🧬")

        text = tricks_biowar["text"]["buy_vaccine"].format(intcomma(fever_price), pet_effect)
        await repo_biowar.buy_vaccine(fever_price, user_id)
        await redis.set(f"epidemic_pet_try_count_heal:{user_id}", 0)
        return await msg.answer(text)

    elif pay_mode == "epi":
        fev_minutes = math.ceil(fev_seconds / 60)
        fever_price = max(1, fev_minutes)

        if lab_info.get("epicoins", 0) < fever_price:
            return await msg.answer(f"❌ Недостаточно эпикоинов! Нужно <b>{fever_price}</b> 🪙")

        await repo_biowar.buy_vaccine_epicoins(fever_price, user_id)
        await redis.set(f"epidemic_pet_try_count_heal:{user_id}", 0)
        text = f"🧪 <b>Вакцина успешно куплена за {fever_price} 🪙 эпикоинов!</b>\n\nВы полностью излечились от болезни."
        return await msg.answer(text)
    id = msg.from_user.id

    lab_info = await repo_biowar.get_info_user_lab(id)

    if not lab_info or not lab_info.get('fever'):
        return await msg.answer(tricks_biowar['infect']['have_not_fever'])

    fev_seconds = (datetime.fromtimestamp(lab_info['fever'], tz=timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    fev_seconds = 1 if fev_seconds <= 0 else fev_seconds

    infecter_row = await repo_biowar.select_one("SELECT victims_owner_id FROM Victims WHERE victim_id = %s;", (id,))
    if infecter_row:
        infecter_id = infecter_row.get("victims_owner_id") if isinstance(infecter_row, dict) else (infecter_row[0] if isinstance(infecter_row, (tuple, list)) else infecter_row)
        infecter_lab = await repo_biowar.get_info_user_lab(infecter_id)
    else:
        infecter_lab = None
    lethality = max(1, int(infecter_lab.get('lethality', 1))) if infecter_lab else max(1, int(lab_info.get('lethality', 1)))
    fever_price_bio, _ = await calculate_vaccine_bio_price(id, lab_info, fev_seconds, repo_biowar)
    fever_price_bio = 1 if fever_price_bio <= 0 else fever_price_bio

    fev_minutes = math.ceil(fev_seconds / 60)
    fever_price_epi = max(1, fev_minutes)

    pet = await repo_biowar.get_my_pet(id)
    if pet and pet.get('current_pet', '').lower() == 'мимин':
        fever_price_bio = max(1, int(fever_price_bio * 0.75))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🧬 {intcomma(fever_price_bio)}", callback_data=f"buy_vac_bio:{id}"),
                InlineKeyboardButton(text=f"🪙 Эпикоины ({intcomma(fever_price_epi)})", callback_data=f"buy_vac_epi:{id}")
            ]
        ]
    )

    text = (
        "🧪 <b>Выбор способа оплаты вакцины</b>\n\n"
        f"☣️ До окончания болезни осталось: <b>{math.ceil(fev_seconds / 60)} мин.</b>\n\n"
        "Выберите удобный способ оплаты:"
    )

    await msg.answer(text, reply_markup=keyboard)


async def cb_buy_vaccine_bio(call: CallbackQuery, db: Cursor, redis: Redis, repo_biowar: RequestsRepoBiowar):
    user_id = call.from_user.id
    target_id = int(call.data.split(":")[1])

    if user_id != target_id:
        return await call.answer("❌ Это не ваша клавиатура!", show_alert=True)

    lab_info = await repo_biowar.get_info_user_lab(user_id)

    if not lab_info or not lab_info.get("fever"):
        return await call.answer("❌ Вы не больны!", show_alert=True)

    fev_seconds = (datetime.fromtimestamp(lab_info["fever"], tz=timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    fev_seconds = 1 if fev_seconds <= 0 else fev_seconds

    pet = await repo_biowar.get_my_pet(user_id)
    pet_effect = ""

    lethality = await get_effective_lethality(user_id, lab_info, repo_biowar)
    fever_price = int(lab_info.get("immunity", 1) * 15)
    fever_price = 1 if fever_price <= 0 else fever_price

    if pet and pet.get("current_pet", "").lower() == "мимин":
        fever_price_base = fever_price
        element_pet_emoji = tricks_biowar["pet"]["pets_info"][pet["current_pet"].lower()]["element_emoji"]
        fever_price = max(1, int(fever_price * 0.75))
        discount = fever_price_base - fever_price
        if discount > 0:
            pet_name = pet["current_pet"].title()
            disc_str = intcomma(discount)
            nl = "\n"
            pet_effect = f"{nl}<b>{element_pet_emoji} {pet_name}</b> снизил расходы вакцины на <b>{disc_str}</b> био-ресурсов"

    if lab_info.get("bio_resource", 0) < fever_price:
        return await call.answer("❌ Недостаточно био-ресурсов!", show_alert=True)

    text = tricks_biowar["text"]["buy_vaccine"].format(intcomma(fever_price), pet_effect)

    await repo_biowar.buy_vaccine(fever_price, user_id)
    await redis.set(f"epidemic_pet_try_count_heal:{user_id}", 0)

    await call.message.edit_text(text)
    await call.answer("✅ Вакцина успешно куплена!")


async def cb_buy_vaccine_epi(call: CallbackQuery, db: Cursor, redis: Redis, repo_biowar: RequestsRepoBiowar):
    user_id = call.from_user.id
    target_id = int(call.data.split(":")[1])

    if user_id != target_id:
        return await call.answer("❌ Это не ваша клавиатура!", show_alert=True)

    lab_info = await repo_biowar.get_info_user_lab(user_id)

    if not lab_info or not lab_info.get("fever"):
        return await call.answer("❌ Вы не больны!", show_alert=True)

    fev_seconds = (datetime.fromtimestamp(lab_info["fever"], tz=timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    fev_seconds = 1 if fev_seconds <= 0 else fev_seconds

    fev_minutes = math.ceil(fev_seconds / 60)
    fever_price = max(1, fev_minutes)

    if lab_info.get("epicoins", 0) < fever_price:
        return await call.answer(f"❌ Недостаточно эпикоинов! Нужно {fever_price} 🪙", show_alert=True)

    await repo_biowar.buy_vaccine_epicoins(fever_price, user_id)
    await redis.set(f"epidemic_pet_try_count_heal:{user_id}", 0)

    text = f"🧪 <b>Вакцина успешно куплена за {fever_price} 🪙 эпикоинов!</b>\n\nВы полностью излечились от болезни."

    await call.message.edit_text(text)
    await call.answer("✅ Вакцина успешно куплена!")

async def victims_list(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    victims = await repo_biowar.get_victims(id)
    victims_food = await repo_biowar.get_victims_food(id)
    infected = await repo_biowar.get_my_infected(id)
    
    victims_list = func.get_victims_list(victims)
    
    text = tricks_biowar['infect']['victims_list'].format(
        '\n'.join(victims_list[0]), infected,
        victims_list[1][0], intcomma(victims_food if victims_food else 0)
    )
    
    await msg.answer(text)

async def illnesses_list(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    illness = await repo_biowar.get_illnesses(id)
    
    illness_list = func.get_illness_list(illness)
    
    text = tricks_biowar['infect']['illnesses_list'].format('\n'.join(illness_list))
    
    await msg.answer(text)

async def add_virus_signal(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    await repo_biowar.update_virus_chat_setup(id, msg.chat.id)
    
    text = tricks_biowar['infect']['add_virus_signal']
    
    await msg.answer(text)

async def del_virus_signal(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    await repo_biowar.del_virus_chat_setup(id)
    
    text = tricks_biowar['infect']['del_virus_signal']
    
    await msg.answer(text)

async def buy_vaccine_joke(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    text = (
        "🚫 <b>Команда больше не работает!</b>\n\n"
        "🚬 Скурить вакцину больше нельзя.\n"
        "💡 Для покупки вакцины используйте команду: <code>!купить вакцину</code>"
    )
    await msg.answer(text)

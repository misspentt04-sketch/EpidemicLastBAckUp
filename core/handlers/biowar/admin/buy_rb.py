from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Bot
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()

ADMIN_ID = 7972320837
LOG_CHAT = -1003688648228

async def send_log(bot: Bot, admin_id: int, target_id: int, levels: int, reset_percent: int, reset_text: str, current_level: int, new_level: int, message_link: str):
    # Лог в группу
    group_text = (
        f"👑 <b>Использована команда /buy_rb</b>\n"
        f"👤 Админ: <code>{admin_id}</code>\n"
        f"🎯 Игрок: <code>{target_id}</code>\n"
        f"📊 Было: {current_level} → Стало: {new_level}\n"
        f"➕ Добавлено: {levels} уровней\n"
        f"🔄 {reset_text}"
    )
    await bot.send_message(LOG_CHAT, group_text, parse_mode="HTML")

    # Лог в ЛС админа с закреплением
    admin_text = (
        f"📩 <b>Уведомление о использовании /buy_rb</b>\n\n"
        f"👤 Админ: <code>{admin_id}</code>\n"
        f"🎯 Игрок: <code>{target_id}</code>\n"
        f"📊 Было: {current_level} → Стало: {new_level}\n"
        f"➕ Добавлено: {levels} уровней\n"
        f"🔄 {reset_text}\n\n"
        f"🔗 <a href='{message_link}'>Ссылка на сообщение</a>"
    )
    msg = await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", disable_web_page_preview=True)
    await bot.pin_chat_message(ADMIN_ID, msg.message_id)

@router.message(Command("buy_rb"))
async def cmd_buy_rb(message: Message, repo_biowar: RequestsRepoBiowar, bot: Bot):
    # Только для админа 7972320837
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    # Если без аргументов — показываем меню
    if len(args) == 1:
        text = (
            "💎 <b>Добавить уровень Rebirth</b>\n\n"
            "Формат: <code>/buy_rb [уровень] [обнуление]</code>\n"
            "Обнуление: <b>0</b> — без обнуления, <b>50</b> — половина, <b>100</b> — полный сброс\n\n"
            "Примеры:\n"
            "<code>/buy_rb 5 0</code> — +5 РБ без обнуления\n"
            "<code>/buy_rb 3 50</code> — +3 РБ, 50% обнуление\n"
            "<code>/buy_rb 1 100</code> — +1 РБ, полный сброс\n\n"
            "Или по ID:\n"
            "<code>/buy_rb 123456789 5 0</code>"
        )
        await message.answer(text, parse_mode="HTML")
        return

    # Определяем цель и параметры
    target_id = None
    levels = 1
    reset_percent = 0

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        if len(args) >= 3:
            try:
                levels = int(args[1])
                reset_percent = int(args[2])
            except ValueError:
                await message.answer("❌ Укажите количество уровней и обнуление цифрами!")
                return
        elif len(args) == 2:
            try:
                levels = int(args[1])
            except ValueError:
                await message.answer("❌ Укажите количество уровней цифрой!")
                return
    else:
        if len(args) >= 4:
            try:
                target_id = int(args[1])
                levels = int(args[2])
                reset_percent = int(args[3])
            except ValueError:
                await message.answer("❌ Укажите ID, количество уровней и обнуление цифрами!")
                return
        elif len(args) == 3:
            try:
                target_id = int(args[1])
                levels = int(args[2])
            except ValueError:
                await message.answer("❌ Укажите ID и количество уровней цифрами!")
                return

    if not target_id:
        await message.answer("❌ Не указана цель! Используйте реплай или укажите ID.")
        return

    if reset_percent not in [0, 50, 100]:
        await message.answer("❌ Обнуление должно быть: <b>0</b> (без), <b>50</b> (половина) или <b>100</b> (полный сброс)", parse_mode="HTML")
        return

    if levels <= 0:
        await message.answer("❌ Количество уровней должно быть больше 0!")
        return

    # Проверяем существование лаборатории
    result = await repo_biowar.cur.execute("SELECT lab_id FROM Lab WHERE lab_id = %s;", (target_id,))
    lab_exists = await repo_biowar.cur.fetchone()
    if not lab_exists:
        await message.answer(f"❌ Пользователь <code>{target_id}</code> не найден в базе!", parse_mode="HTML")
        return

    # Получаем текущий уровень и ресурсы
    result = await repo_biowar.cur.execute("""
        SELECT rebirth_level, bio_experience, bio_resource 
        FROM Lab WHERE lab_id = %s
    """, (target_id,))
    lab_data = await repo_biowar.cur.fetchone()
    
    if not lab_data:
        await message.answer("❌ Лаборатория не найдена!")
        return

    current_level = lab_data[0] if isinstance(lab_data, (tuple, list)) else lab_data.get('rebirth_level', 0) or 0
    new_level = current_level + levels

    # Обновляем rebirth_level
    await repo_biowar.cur.execute("UPDATE Lab SET rebirth_level = %s WHERE lab_id = %s;", (new_level, target_id))

    # Обнуление
    reset_text = "без обнуления"
    if reset_percent == 50:
        current_exp = lab_data[1] if isinstance(lab_data, (tuple, list)) else lab_data.get('bio_experience', 0) or 0
        current_bio = lab_data[2] if isinstance(lab_data, (tuple, list)) else lab_data.get('bio_resource', 0) or 0
        await repo_biowar.cur.execute("""
            UPDATE Lab 
            SET bio_experience = %s,
                bio_resource = %s
            WHERE lab_id = %s
        """, (int(current_exp * 0.5), int(current_bio * 0.5), target_id))
        reset_text = "50% обнуление (половина сохранена)"
    elif reset_percent == 100:
        start_exp = 1000 + (new_level - 1) * 1000
        start_bio = 15000 + (new_level - 1) * 10000
        await repo_biowar.cur.execute("""
            UPDATE Lab 
            SET bio_experience = %s,
                bio_resource = %s
            WHERE lab_id = %s
        """, (start_exp, start_bio, target_id))
        reset_text = "100% обнуление (полный сброс)"

    await repo_biowar.cur.connection.commit()

    # Создаём ссылку на сообщение
    message_link = f"https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id}"

    # Отправляем логи
    await send_log(
        bot,
        message.from_user.id,
        target_id,
        levels,
        reset_percent,
        reset_text,
        current_level,
        new_level,
        message_link
    )

    await message.answer(
        f"🎉 <b>REBIRTH ДОБАВЛЕН!</b>\n\n"
        f"👤 Игрок: <code>{target_id}</code>\n"
        f"📊 Было: <b>{current_level}</b> → Стало: <b>{new_level}</b>\n"
        f"➕ Добавлено: <b>{levels}</b> уровней\n"
        f"🔄 {reset_text}\n\n"
        f"✅ Бонусы перерождения активированы!",
        parse_mode="HTML"
    )

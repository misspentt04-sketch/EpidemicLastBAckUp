from aiogram import Router, F
from aiogram.types import Message
from core.handlers.tricks.themes import get_user_bought_themes, save_bought_themes, set_user_theme

admin_theme_router = Router()

@admin_theme_router.message(F.text.startswith("!выдать тему") | F.text.startswith("/givetheme"))
async def give_admin_theme_handler(msg: Message, db=None):
    args = msg.text.split()
    
    target_id = None
    theme_id = None

    # Вариант 1: Ответом на сообщение (Reply) -> !выдать тему admin
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        # Если команда начинается с !выдать тему, название темы будет 3-м аргументом (индекс 2)
        if args[0].lower() in ["!выдать", "/givetheme"] and len(args) >= 3:
            theme_id = args[2].lower()
        elif len(args) >= 2:
            theme_id = args[1].lower()

    # Вариант 2: Прямым текстом с ID -> !выдать тему 7972320837 admin
    else:
        # Для "!выдать тему 7972320837 admin" длина args равна 4
        if args[0].lower() == "!выдать" and len(args) >= 4:
            try:
                target_id = int(args[2])
                theme_id = args[3].lower()
            except ValueError:
                return await msg.answer("❌ Неверный формат User ID.")
        # Для "/givetheme 7972320837 admin" длина args равна 3
        elif args[0].lower() == "/givetheme" and len(args) >= 3:
            try:
                target_id = int(args[1])
                theme_id = args[2].lower()
            except ValueError:
                return await msg.answer("❌ Неверный формат User ID.")

    if not target_id or not theme_id:
        return await msg.answer(
            "⚠️ <b>Использование команды:</b>\n\n"
            "1. <code>!выдать тему <ID> <тема></code>\n"
            "Пример: <code>!выдать тему 7972320837 admin</code>\n\n"
            "2. Ответом на сообщение: <code>!выдать тему <тема></code>\n"
            "Пример: <code>!выдать тему admin</code>"
        )

    bought = await get_user_bought_themes(db, target_id)
    if theme_id not in bought:
        bought.append(theme_id)
        await save_bought_themes(db, target_id, bought)

    await set_user_theme(db, target_id, theme_id)
    await msg.answer(
        f"👑 Тема <b>{theme_id}</b> успешно выдана и активирована для пользователя <code>{target_id}</code>!"
    )


@admin_theme_router.message(F.text.startswith("!забрать тему") | F.text.startswith("/taketheme"))
async def take_admin_theme_handler(msg: Message, db=None):
    args = msg.text.split()
    target_id = None
    theme_id = None

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        if args[0].lower() in ["!забрать", "/taketheme"] and len(args) >= 3:
            theme_id = args[2].lower()
        elif len(args) >= 2:
            theme_id = args[1].lower()
    else:
        if args[0].lower() == "!забрать" and len(args) >= 4:
            try:
                target_id = int(args[2])
                theme_id = args[3].lower()
            except ValueError:
                return await msg.answer("❌ Неверный формат User ID.")
        elif args[0].lower() == "/taketheme" and len(args) >= 3:
            try:
                target_id = int(args[1])
                theme_id = args[2].lower()
            except ValueError:
                return await msg.answer("❌ Неверный формат User ID.")

    if not target_id or not theme_id:
        return await msg.answer(
            "⚠️ <b>Использование команды:</b>\n\n"
            "1. <code>!забрать тему <ID> <тема></code>\n"
            "Пример: <code>!забрать тему 7972320837 police</code>\n\n"
            "2. Ответом на сообщение: <code>!забрать тему <тема></code>"
        )

    bought = await get_user_bought_themes(db, target_id)
    if theme_id in bought:
        bought.remove(theme_id)
        await save_bought_themes(db, target_id, bought)

    current_theme = await get_user_theme(db, target_id)
    if current_theme == theme_id:
        await set_user_theme(db, target_id, "default")

    await msg.answer(
        f"🗑 Тема <b>{theme_id}</b> успешно изъята у пользователя <code>{target_id}</code>! "
        f"(Если она была активной, установлена тема по умолчанию)."
    )

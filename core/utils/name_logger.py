import time


LOG_CHAT_ID = -1003688648228


async def log_name_change(repo, user_id: int, field: str, old_value, new_value, bot=None):
    """
    Логирует смену имени лаборатории/патогена:
    - пишет в NameHistory
    - шлёт сообщение в LOG_CHAT_ID (если передан bot)
    """
    field_ru = {
        "lab_name": "лаборатории",
        "pathogen_name": "патогена",
    }.get(field, field)

    # 1. Запись в историю
    try:
        await repo.cur.execute(
            "INSERT INTO NameHistory (user_id, field, old_value, new_value, changed_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, field, old_value, new_value, int(time.time())),
        )
    except Exception as e:
        print(f"[NAME HISTORY ERROR] {e}")

    # 2. Получаем username/full_name
    uname = None
    fname = None
    try:
        await repo.cur.execute(
            "SELECT username, full_name FROM Users WHERE id = %s", (user_id,)
        )
        urow = await repo.cur.fetchone()
        if urow:
            if isinstance(urow, dict):
                uname = urow.get("username")
                fname = urow.get("full_name")
            else:
                uname = urow[0] if len(urow) > 0 else None
                fname = urow[1] if len(urow) > 1 else None
    except Exception as e:
        print(f"[NAME LOG USER ERROR] {e}")

    def esc(x):
        if x is None or x == "":
            return "<i>не задано</i>"
        return f"<code>{x}</code>"

    if uname:
        who = f'<a href="https://t.me/{uname}">{fname or uname}</a>'
    else:
        who = f'<a href="tg://user?id={user_id}">{fname or user_id}</a>'

    text = (
        f"📝 <b>Игрок изменил имя {field_ru}</b>\n\n"
        f"👤 {who} (<code>{user_id}</code>)\n"
        f"🔄 <b>Было:</b> {esc(old_value)}\n"
        f"✅ <b>Стало:</b> {esc(new_value)}"
    )

    # 3. Отправка в чат
    if bot is not None:
        try:
            await bot.send_message(
                LOG_CHAT_ID, text, parse_mode="HTML", disable_web_page_preview=True
            )
        except Exception as e:
            print(f"[NAME LOG SEND ERROR] {e}")

    return text

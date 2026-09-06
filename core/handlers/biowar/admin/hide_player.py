from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()

@router.message(F.text.lower().startswith("!скрыть"))
async def cmd_hide_player(msg: Message, repo_biowar: RequestsRepoBiowar):
    if msg.from_user.id not in [7972320837]:
        return

    args = msg.text.split()
    target_id = None

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
    else:
        if len(args) >= 2:
            try:
                target_id = int(args[1])
            except ValueError:
                pass

    if not target_id:
        await msg.reply("❌ Использование: !скрыть @username или !скрыть 123456789 (реплаем на сообщение)")
        return

    # Проверяем существование
    result = await repo_biowar.cur.execute("SELECT lab_id FROM Lab WHERE lab_id = %s;", (target_id,))
    lab = await repo_biowar.cur.fetchone()
    if not lab:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден!")
        return

    # Добавляем в скрытые
    await repo_biowar.cur.execute("""
        INSERT INTO HiddenPlayers (lab_id, hidden_by)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            hidden_by = VALUES(hidden_by),
            hidden_at = UNIX_TIMESTAMP()
    """, (target_id, msg.from_user.id))
    await repo_biowar.cur.connection.commit()

    await msg.reply(f"✅ Игрок <code>{target_id}</code> скрыт во всех топах!")

@router.message(F.text.lower().startswith("!показать"))
async def cmd_show_player(msg: Message, repo_biowar: RequestsRepoBiowar):
    if msg.from_user.id not in [7972320837]:
        return

    args = msg.text.split()
    target_id = None

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
    else:
        if len(args) >= 2:
            try:
                target_id = int(args[1])
            except ValueError:
                pass

    if not target_id:
        await msg.reply("❌ Использование: !показать @username или !показать 123456789 (реплаем на сообщение)")
        return

    await repo_biowar.cur.execute("DELETE FROM HiddenPlayers WHERE lab_id = %s;", (target_id,))
    await repo_biowar.cur.connection.commit()
    await msg.reply(f"✅ Игрок <code>{target_id}</code> снова виден во всех топах!")

@router.message(Command("hidden_list"))
@router.message(F.text.lower().startswith("!скрытые"))
async def cmd_hidden_list(msg: Message, repo_biowar: RequestsRepoBiowar):
    if msg.from_user.id not in [7972320837]:
        return

    await repo_biowar.cur.execute("""
        SELECT h.lab_id, h.hidden_at, u.full_name, u.username
        FROM HiddenPlayers h
        LEFT JOIN Users u ON u.id = h.lab_id
        ORDER BY h.hidden_at DESC
    """)
    rows = await repo_biowar.cur.fetchall()

    if not rows:
        await msg.answer("📭 Скрытых игроков нет.")
        return

    text = "👻 <b>Скрытые игроки:</b>\n\n"
    for row in rows:
        lab_id = row[0]
        hidden_at = row[1]
        full_name = row[2] or "Без имени"
        username = row[3] or ""

        from datetime import datetime
        date_str = datetime.fromtimestamp(hidden_at).strftime("%d.%m.%Y %H:%M") if hidden_at else "—"

        name_display = f"@{username}" if username else full_name
        text += f"• <code>{lab_id}</code> — {name_display} (скрыт {date_str})\n"

    await msg.answer(text, parse_mode="HTML")

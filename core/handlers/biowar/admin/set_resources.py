from aiogram import types, F, Router
from aiogram.types import Message

router = Router()

@router.message(F.text.lower().startswith("!установить ресы"))
async def set_resources_cmd(msg: types.Message, db):
    if msg.from_user.id != 7972320837:
        await msg.reply("❌ У вас нет прав на эту команду!")
        return

    args = msg.text.split()
    target_id = None
    amount = 0

    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        for arg in args:
            if arg.lstrip('-').isdigit():
                amount = int(arg)
                break
    else:
        for arg in args:
            if arg.startswith('@'):
                username = arg[1:]
                await db.execute("SELECT id FROM Users WHERE username = %s", (username,))
                row = await db.fetchone()
                if row:
                    # Исправлено: проверяем тип row
                    if isinstance(row, dict):
                        target_id = row.get('id')
                    else:
                        target_id = row[0] if isinstance(row, (tuple, list)) else row.get('id')
                continue
            elif arg.lstrip('-').isdigit() and len(arg) > 4:
                if not target_id:
                    target_id = int(arg)
                else:
                    amount = int(arg)

    if not target_id:
        await msg.reply("❌ Укажите ID пользователя или username")
        return

    await db.execute("UPDATE Lab SET bio_resource = %s WHERE lab_id = %s", (amount, target_id))
    await db.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (target_id,))
    row = await db.fetchone()
    
    # Исправлено: универсальная проверка row
    if row:
        if isinstance(row, dict):
            new_balance = row.get('bio_resource', 0)
        elif isinstance(row, (tuple, list)):
            new_balance = row[0] if len(row) > 0 else 0
        else:
            new_balance = 0
    else:
        new_balance = 0

    await msg.reply(
        f"✅ Установлено <b>{amount:,} 🧬</b>\n"
        f"📥 Пользователю: <code>{target_id}</code>\n"
        f"📊 Текущий баланс: <b>{new_balance:,}</b>",
        parse_mode="HTML"
    )

import pyrogram
from pyrogram import Client, filters

ALLOWED_ADMINS = [7972320837, 8236324289]

async def guard_filter(_, client, message):
    if not message.from_user:
        return False
    if message.from_user.id in ALLOWED_ADMINS:
        return True
    try:
        await message.reply_text("🛠 Бот находится на технических работах.")
    except Exception:
        pass
    return False

admin_only = filters.create(guard_filter)

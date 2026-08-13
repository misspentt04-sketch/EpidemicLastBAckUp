import os
from aiogram import Router, F
from aiogram.types import Message

router = Router()
MAINTENANCE_FILE = "/home/ubuntu/epidemic/maintenance.flag"
ALLOWED_USERS = {7972320837, 7958133684}

@router.message(F.text.in_({"+тех", "-тех", "/tech_on", "/tech_off"}))
async def cmd_toggle_tech(message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        return

    text = message.text.strip().lower()
    if text in ("+тех", "/tech_on"):
        with open(MAINTENANCE_FILE, "w") as f:
            f.write("1")
        await message.answer("🛠 <b>Технические работы успешно ВКЛЮЧЕНЫ.</b>\nБот отвечает только владельцам.", parse_mode="HTML")
    elif text in ("-тех", "/tech_off"):
        if os.path.exists(MAINTENANCE_FILE):
            os.remove(MAINTENANCE_FILE)
        await message.answer("✅ <b>Технические работы ОТКЛЮЧЕНЫ.</b>\nБот снова доступен для всех.", parse_mode="HTML")

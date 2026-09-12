import asyncio
from aiogram import Bot

BOT_TOKEN = "8879844317:AAEtxKO3Aq-ZkKxDLULBP9QZ6-o6w1g8NJA"
LOG_CHAT = -1004335676077

async def main():
    bot = Bot(token=BOT_TOKEN)
    text = (
        "🏆 <b>Босс повержен — награды выданы!</b>\n\n"
        "🥇 <code>2088966314</code> — <b>34,200</b> урона\n"
        "    🎁 +10,000 опыта, +3 кейса, +1,000 🪙\n"
        "🥈 <code>8513384565</code> — <b>33,832</b> урона\n"
        "    🎁 +3,000 опыта, +1 кейс, +500 🪙\n"
        "🥉 <code>826461867</code> — <b>23,320</b> урона\n"
        "    🎁 +1,000 опыта, +300 🪙\n\n"
        "📊 Всего атакующих: <b>10</b>"
    )
    await bot.send_message(LOG_CHAT, text, parse_mode="HTML")
    await bot.session.close()
    print("✅ Уведомление отправлено")

asyncio.run(main())

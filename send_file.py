import asyncio
from aiogram import Bot
from aiogram.types import FSInputFile
from core.settings import settings

async def send():
    bot = Bot(token=settings.bots.bot_token)
    file = FSInputFile("core/data/tricks/themes_data.py")
    await bot.send_document(
        chat_id=7972320837,
        document=file,
        caption="📄 Файл themes_data.py"
    )
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(send())

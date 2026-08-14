import sys
import os
import asyncio
from pathlib import Path

# Добавляем корень проекта в путь импорта
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from aiogram import Bot
from aiogram.types import FSInputFile

# Вставляем токен напрямую
BOT_TOKEN = "8807559002:AAFi2GdF8PFtYZ0jj8S9eW2T9efR79WMn-c"

bot = Bot(token=BOT_TOKEN)

async def main():
    export_filename = "all_themes_export.txt"
    admin_id = 7972320837
    path_to_file = "core/data/tricks/themes_data.py"
    
    # Читаем содержимое файла с темами
    if os.path.exists(path_to_file):
        with open(path_to_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print(f"❌ Файл {path_to_file} не найден!")
        return

    # Записываем в текстовый файл для экспорта
    with open(export_filename, "w", encoding="utf-8") as f:
        f.write(content)

    # Отправляем файл в Telegram
    await bot.send_document(
        chat_id=admin_id,
        document=FSInputFile(export_filename, filename="all_themes_export.txt"),
        caption="📄 Экспорт всех тем из themes_data.py"
    )
    
    # Удаляем временный экспортный файл
    if os.path.exists(export_filename):
        os.remove(export_filename)
        
    print("✅ Файл с темами успешно отправлен в Telegram!")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

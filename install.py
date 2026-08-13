import os

MODULE_CODE = '''from pyrogram import Client, filters
from pyrogram.types import Message
import re

MY_TELEGRAM_ID = 7972320837

def register_lab_handlers(app: Client):
    @app.on_message(filters.command("add") & filters.reply)
    async def process_lab_dossier(client: Client, message: Message):
        if message.from_user and message.from_user.id != MY_TELEGRAM_ID:
            return

        target = message.reply_to_message
        text = target.text or target.caption
        if not text:
            await message.reply_text("❌ В отвеченном сообщении нет текста.")
            return

        new_text = text
        new_text = new_text.replace("Досье Синдиката:", "📩 Досье лаборатории с нуля опыта в топы:")
        new_text = new_text.replace("Дон (Глава)", "Руководитель")
        new_text = new_text.replace("Метод рэкета:", "Имя патогена:")
        new_text = new_text.replace("Готовых бойцов:", "Готовых патогенов:")
        new_text = new_text.replace("Квалификация Капо:", "Квалификация учёных:")
        new_text = new_text.replace("Новый боец через", "Новый патоген через")

        new_text = new_text.replace("Характеристики Синдиката", "Характеристика")
        new_text = new_text.replace("Влияние и напор:", "Заразность:")
        new_text = new_text.replace("Связи и крыша:", "Иммунитет:")
        new_text = new_text.replace("Жестокость наказаний:", "Летальность:")
        new_text = new_text.replace("Личная охрана Дона:", "Служба безопасности:")

        # Фикс отступов (убираем лишние \n\n)
        new_text = re.sub(r'\n+\s*-{5,}\s*\n+', '\n-------------------\n', new_text)
        new_text = new_text.replace("ID синдиката:", "ID лаборатории:")

        new_text = new_text.replace("Общак и Касса", "Запасы — реагентов")
        new_text = new_text.replace("Авторитет:", "Опыт:")
        new_text = new_text.replace("Чёрный безнал:", "Ресурсы:")
        new_text = new_text.replace("Ежедневная дань через:", "Ежедневная премия через:")
        new_text = new_text.replace("Подконтрольных точек:", "😏 Заражённых:")
        new_text = new_text.replace("Наездов на вас:", "😷 Своих болезней:")

        await message.reply_text(new_text)
'''

def install():
    with open("lab_converter.py", "w", encoding="utf-8") as f:
        f.write(MODULE_CODE)
    print("✅ Файл 'lab_converter.py' успешно создан.")

    main_files = ["main.py", "bot.py", "app.py"]
    target_main = None

    for fname in main_files:
        if os.path.exists(fname):
            target_main = fname
            break

    if not target_main:
        print("⚠️ Главный файл (main.py/bot.py) не найден. Добавьте импорт вручную:")
        print("   from lab_converter import register_lab_handlers")
        print("   register_lab_handlers(app)")
        return

    with open(target_main, "r", encoding="utf-8") as f:
        content = f.read()

    if "from lab_converter import register_lab_handlers" in content:
        print(f"ℹ️ Модуль уже подключен в {target_main}.")
        return

    import_line = "from lab_converter import register_lab_handlers\n"
    register_call = "\n# Регистрация модуля конвертера лаборатории\nregister_lab_handlers(app)\n"

    if "app.run(" in content:
        content = import_line + content
        content = content.replace("app.run(", register_call + "\napp.run(")
    elif "idle()" in content:
        content = import_line + content
        content = content.replace("idle()", register_call + "\nidle()")
    else:
        content = import_line + content + register_call

    with open(target_main, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Модуль успешно подключен в '{target_main}'!")

if __name__ == "__main__":
    install()

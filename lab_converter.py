from pyrogram import Client, filters
from pyrogram.types import Message
import re

def register_lab_handlers(app: Client):

    @app.on_message((filters.me | filters.incoming) & filters.command(["add", "add@Epidemic_bot"], prefixes=["/", "!", "."]) & filters.reply)
    async def process_lab_dossier(client: Client, message: Message):
        target = message.reply_to_message
        text = target.text or target.caption
        if not text:
            await message.reply_text("❌ В отвеченном сообщении нет текста.")
            return

        # 1. Шапка (поддержка как Синдиката, так и стандартной Лабы)
        text = re.sub(r"📩 Досье лаборатории .*?:", "📩 Досье лаборатории с нуля опыта в топы:", text)
        text = text.replace("🍷 Досье Синдиката:", "📩 Досье лаборатории с нуля опыта в топы:")
        text = text.replace("Дон (Глава)", "Руководитель")

        # 2. Имя и Патогены
        text = text.replace("🏷 Метод рэкета:", "🏷 Имя патогена:")
        text = text.replace("Метод рэкета:", "🏷 Имя патогена:")
        text = text.replace("🧪 Готовых бойцов:", "🧪 Готовых патогенов:")
        text = text.replace("Готовых бойцов:", "🧪 Готовых патогенов:")

        # 3. Квалификация
        text = text.replace("🕵️ Квалификация Капо:", "🧑‍🔬 Квалификация учёных:")
        text = text.replace("Квалификация Капо:", "🧑‍🔬 Квалификация учёных:")
        text = text.replace("⏳ Новый боец через", "⏳ Новый патоген через")
        text = text.replace("Новый боец через", "⏳ Новый патоген через")

        # 4. Характеристики
        text = text.replace("——[ Характеристики Синдиката ]——", "——[ Характеристика]——")
        text = text.replace("——[ Характеристика ]——", "——[ Характеристика]——")
        text = text.replace("🗡 Влияние и напор:", "💉 Заразность:")
        text = text.replace("Влияние и напор:", "💉 Заразность:")
        text = text.replace("✋ Связи и крыша:", "✋ Иммунитет:")
        text = text.replace("Связи и крыша:", "✋ Иммунитет:")
        text = text.replace("💊 Жестокость наказаний:", "💊 Летальность:")
        text = text.replace("Жестокость наказаний:", "💊 Летальность:")
        text = text.replace("🕵️ Личная охрана Дона:", "🕵️ Служба безопасности:")
        text = text.replace("Личная охрана Дона:", "🕵️ Служба безопасности:")

        # 5. Разделители и ID
        text = re.sub(r'\n+\s*-{5,}\s*\n+', '\n-------------------\n', text)
        text = text.replace("ID синдиката:", "ID лаборатории:")

        # 6. Запасы и Финансы
        text = text.replace("——[ Общак и Касса ]——", "—[Запасы — реагентов]—")
        text = text.replace("——[Запасы — реагентов]——", "—[Запасы — реагентов]—")
        text = text.replace("☣️ Авторитет:", "☣️ Опыт:")
        text = text.replace("Авторитет:", "☣️ Опыт:")
        text = text.replace("🧬 Чёрный безнал:", "🧬 Ресурсы:")
        text = text.replace("Чёрный безнал:", "🧬 Ресурсы:")
        text = text.replace("⏱ Ежедневная дань через:", "⏱ Ежедневная премия через:")
        text = text.replace("Ежедневная дань через:", "⏱ Ежедневная премия через:")

        # 7. Статусы и Болезни
        text = text.replace("😏 Подконтрольных точек:", "😏 Заражённых:")
        text = text.replace("Подконтрольных точек:", "😏 Заражённых:")
        text = text.replace("Заражённых:", "😏 Заражённых:")
        text = text.replace("😏 😏", "😏") # защита от дублирования emoji

        text = text.replace("😷 Наездов на вас:", "😷 Своих болезней:")
        text = text.replace("Наездов на вас:", "😷 Своих болезней:")
        text = text.replace("Своих болезней:", "😷 Своих болезней:")
        text = text.replace("😷 😷", "😷") # защита от дублирования emoji

        # 8. Фикс горячки / лихорадки
        text = text.replace("🤒 Ученый в состоянии горячки", "🤒 Ученый в состоянии горячки")

        await message.reply_text(text)

import io
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()

MY_ID = 7972320837

@router.message(F.from_user.id == MY_ID, F.text.in_({"/topexp", "!topexp", "topexp"}))
async def cmd_my_top_exp(message: Message, repo_biowar: RequestsRepoBiowar):
    msg = await message.answer("⏳ Собираю полный топ лабораторий...")
    try:
        data = await repo_biowar.get_lab_biotop()
        if not data:
            return await msg.edit_text("❌ Данные лабораторий не найдены.")

        # Начинаем содержимое файла с заголовка
        lines = ["🔬 Топ Лабораторий по био-опыту:", ""]

        count = 1
        for row in data:
            lab_id = row.get("lab_id") or row.get("user_id") or row.get("id")
            exp = row.get("bio_experience", 0)

            # Проверка на корректность ID игрока (реальный положительный ID)
            if not lab_id or not str(lab_id).lstrip("-").isdigit():
                continue

            lab_id_int = int(lab_id)
            if lab_id_int <= 0:
                continue

            line = f"{count}. @{lab_id_int} | {exp}"
            lines.append(line)
            count += 1

        # Добавляем __f в самом конце
        lines.append("__f")

        file_content = "\n".join(lines).encode("utf-8")
        document = BufferedInputFile(file_content, filename="top_bio_exp.txt")

        # Отправляем файл без текста подписи
        await msg.delete()
        await message.answer_document(
            document=document
        )
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка при формировании файла: {e}")

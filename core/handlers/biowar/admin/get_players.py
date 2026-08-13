from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command

router = Router()

ADMIN_IDS = [8879844317, 7972320837, 8236324289]

@router.message(Command("get_players"))
async def cmd_get_players(message: Message, repo_biowar):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    try:
        await repo_biowar.cur.execute("SELECT id FROM Users   ORDER BY id DESC;")
        rows = await repo_biowar.cur.fetchall()
    except Exception as e:
        await message.answer(f"❌ Ошибка базы данных: <code>{e}</code>", parse_mode="HTML")
        return

    if not rows:
        await message.answer("📭 <b>Список игроков пуст.</b>", parse_mode="HTML")
        return

    lines = []
    for idx, row in enumerate(rows, 1):
        if isinstance(row, dict):
            user_id = row.get("id")
        elif isinstance(row, (list, tuple)):
            user_id = row[0]
        else:
            user_id = row

        lines.append(f"{idx}. @{user_id}")

    file_content = "\n".join(lines).encode("utf-8")
    document = BufferedInputFile(file_content, filename="players.txt")

    await message.answer_document(
        document=document,
        caption="📋 <b>Список ID игроков</b>",
        parse_mode="HTML"
    )

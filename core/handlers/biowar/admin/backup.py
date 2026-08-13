import json
import os
import asyncio
from datetime import datetime
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command, CommandObject

router = Router()

ADMIN_IDS = [8879844317, 7972320837, 8236324289]

# Конфигурация для дампов БД
DB_USER = "root"
DB_PASS = "1603"
DB_NAME = "epidemic"

async def extract_target_user_id(message: Message, command: CommandObject, repo_biowar) -> int | None:
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    if not command.args:
        return None

    arg = command.args.strip()

    if arg.isdigit() or (arg.startswith("-") and arg[1:].isdigit()):
        return int(arg)

    username = arg.lstrip("@")
    try:
        if hasattr(repo_biowar, "get_id_by_username"):
            res = await repo_biowar.get_id_by_username(username)
            if res:
                return res.get("id") if isinstance(res, dict) else res
    except Exception:
        pass

    try:
        await repo_biowar.cur.execute("SELECT id FROM Users WHERE username = %s LIMIT 1;", (username,))
        row = await repo_biowar.cur.fetchone()
        if row:
            return row.get("id") if isinstance(row, dict) else row[0]
    except Exception:
        pass

    return None

@router.message(Command("backup"))
async def cmd_backup(message: Message, command: CommandObject, repo_biowar):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    target_id = await extract_target_user_id(message, command, repo_biowar)
    if not target_id:
        await message.answer("❌ <b>Укажите пользователя:</b> аргументом (<code>/backup 123456</code>), через <code>@username</code> или ответом на сообщение.", parse_mode="HTML")
        return

    try:
        await repo_biowar.cur.execute("SELECT * FROM Victims WHERE victims_owner_id = %s;", (target_id,))
        rows = await repo_biowar.cur.fetchall()
    except Exception as e:
        await message.answer(f"❌ Ошибка базы данных: <code>{e}</code>", parse_mode="HTML")
        return

    if not rows:
        await message.answer(f"📭 У пользователя <code>{target_id}</code> нет жертв.", parse_mode="HTML")
        return

    result = {}
    for row in rows:
        if isinstance(row, dict):
            v_id = str(row.get("victim_id") or row.get("id"))
            exp_val = row.get("victim_bio_resource_earn") or 0
            date_val = row.get("infect_date") or 0
            until_val = row.get("victim_expire") or 0
        else:
            v_id = str(row[2]) if len(row) > 2 else str(row[0])
            until_val = row[3] if len(row) > 3 else 0
            date_val = row[4] if len(row) > 4 else 0
            exp_val = row[6] if len(row) > 6 else 0

        date_ts = int(date_val.timestamp()) if hasattr(date_val, "timestamp") else int(date_val or 0)
        until_ts = int(until_val.timestamp()) if hasattr(until_val, "timestamp") else int(until_val or 0)

        result[v_id] = {
            "exp": int(exp_val),
            "date": date_ts,
            "until": until_ts
        }

    json_str = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    file_bytes = json_str.encode("utf-8")

    document = BufferedInputFile(file_bytes, filename=f"backup_{target_id}.json")
    await message.answer_document(
        document=document,
        caption=f"📦 <b>Бэкап жертв игрока</b> <code>{target_id}</code>",
        parse_mode="HTML"
    )

@router.message(Command("db_backup"))
async def cmd_db_backup(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    status_msg = await message.answer("⏳ <i>Создаю полный бэкап базы данных...</i>", parse_mode="HTML")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"epidemic_db_{timestamp}.sql.gz"
    backup_path = f"/tmp/{backup_filename}"

    # Команда дампа MySQL
    dump_cmd = f"mysqldump -u {DB_USER} -p{DB_PASS} {DB_NAME} | gzip > {backup_path}"

    try:
        process = await asyncio.create_subprocess_shell(dump_cmd)
        await process.communicate()

        if process.returncode != 0:
            await status_msg.edit_text("❌ Ошибка при создании дампа MySQL.")
            return

        # Чтение и отправка файла
        with open(backup_path, "rb") as f:
            file_bytes = f.read()

        document = BufferedInputFile(file_bytes, filename=backup_filename)
        await message.answer_document(
            document=document,
            caption=f"📦 <b>Полный бэкап БД</b> <code>{DB_NAME}</code>\n📅 <i>{timestamp}</i>",
            parse_mode="HTML"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка выгрузки: <code>{e}</code>", parse_mode="HTML")

    finally:
        if os.path.exists(backup_path):
            os.remove(backup_path)

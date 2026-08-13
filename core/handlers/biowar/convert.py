import json
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from core.utils.db_api.settings_pool import db_pool

router = Router()

ALLOWED_ADMINS = [7972320837, 7958133684, 8236324289]

@router.message(F.text.regexp(r'^/(convert|victims)(\s|$)'))
async def cmd_convert(message: Message):
    if message.from_user.id not in ALLOWED_ADMINS:
        await message.answer("❌ У вас нет прав на использование этой команды.")
        return

    target_user_id = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            arg = args[1].strip()
            if arg.startswith('@'):
                username = arg[1:]
                pool = await db_pool.get_pool()
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute('SELECT id FROM Users WHERE username = %s;', (username,))
                        row = await cur.fetchone()
                        if row:
                            target_user_id = row.get('id') if isinstance(row, dict) else row[0]
            else:
                try:
                    target_user_id = int(arg)
                except ValueError:
                    pass

    if not target_user_id:
        target_user_id = message.from_user.id

    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT victim_id, infect_date, victim_expire, victim_bio_resource_earn 
                FROM Victims 
                WHERE victims_owner_id = %s;
            """, (target_user_id,))
            rows = await cur.fetchall()

    result_data = {}
    for row in rows:
        victim_id = str(row.get('victim_id') if isinstance(row, dict) else row[0])
        date_ts = int(row.get('infect_date') if isinstance(row, dict) else row[1])
        until_ts = int(row.get('victim_expire') if isinstance(row, dict) else row[2])
        exp_val = int(row.get('victim_bio_resource_earn') if isinstance(row, dict) else row[3])

        result_data[victim_id] = {
            "exp": exp_val,  
            "date": date_ts,
            "until": until_ts
        }

    json_output = json.dumps(result_data, ensure_ascii=False, separators=(',', ':'))

    file_path = f"/tmp/victims_{target_user_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_output)

    await message.answer_document(
        FSInputFile(file_path), 
        caption=f"📁 Список жертв для ID: {target_user_id}"
    )

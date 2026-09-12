from aiogram import Router, F
from aiogram.types import Message
from redis.asyncio import Redis

router = Router()

ADMIN_ID = 7972320837


@router.message(F.text.lower() == "!активность")
async def cmd_activity(msg: Message, redis: Redis):
    if msg.from_user.id != ADMIN_ID:
        return

    keys = await redis.keys("activity:*")
    if not keys:
        await msg.reply("📊 <b>Активность за 10 минут:</b>\n\n<i>Нет данных.</i>", parse_mode="HTML")
        return

    stats = []
    for k in keys:
        uid = k.split(":")[1]
        cnt = int(await redis.get(k) or 0)
        stats.append((uid, cnt))

    stats.sort(key=lambda x: x[1], reverse=True)

    lines = ["📊 <b>Активность за 10 минут:</b>\n"]
    total = 0
    for i, (uid, cnt) in enumerate(stats[:20], 1):
        lines.append(f"{i}. <code>{uid}</code> — <b>{cnt}</b> команд")
        total += cnt

    lines.append(f"\n👥 <b>Всего юзеров:</b> {len(stats)}")
    lines.append(f"📨 <b>Всего команд:</b> {total}")

    await msg.reply("\n".join(lines), parse_mode="HTML")

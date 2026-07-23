import random
from aiogram import Router, types, F
from aiogram.filters import Command
from core.settings import settings

promos_router = Router()

is_admin = lambda msg: str(msg.from_user.id) in settings.bots.admin_id

async def ensure_promo_table(db):
    await db.execute("""
        CREATE TABLE IF NOT EXISTS Promos (
            code VARCHAR(64) PRIMARY KEY,
            activations_left INT NOT NULL,
            reward_type VARCHAR(32) NOT NULL,
            reward_value INT NOT NULL
        );
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS PromoActivations (
            code VARCHAR(64),
            user_id BIGINT,
            PRIMARY KEY (code, user_id)
        );
    """)

# ==================== 1. СОЗДАНИЕ ПРОМОКОДА (АДМИН) ====================
@promos_router.message(Command("add_promo"))
async def cmd_add_promo(msg: types.Message, db):
    if not is_admin(msg):
        await msg.reply("❌ У вас нет прав для создания промокодов!")
        return

    await ensure_promo_table(db)
    args = msg.text.split()
    
    if len(args) < 5:
        await msg.reply(
            "💡 <b>Использование:</b>\n"
            "<code>/add_promo [код] [кол-во активаций] [тип] [значение]</code>\n\n"
            "📌 <b>Типы:</b> кейс, донаткейс, коины, зз, иммун, летал, пат, сб"
        )
        return

    code = args[1].upper()
    try:
        activations = int(args[2])
        value = int(args[4])
    except ValueError:
        await msg.reply("❌ Количество активаций и значение должны быть числами!")
        return

    raw_type = args[3].lower()
    type_map = {
        "кейс": "case1",
        "донаткейс": "case2",
        "донат": "case2",
        "коины": "epicoins",
        "эпикоины": "epicoins",
        "зз": "infect",
        "иммун": "immunity",
        "летал": "lethality",
        "пат": "pathogens",
        "сб": "security_service"
    }

    if raw_type not in type_map:
        await msg.reply(f"❌ Неизвестный тип награды: <code>{raw_type}</code>")
        return

    reward_type = type_map[raw_type]

    try:
        await db.execute(
            "INSERT INTO Promos (code, activations_left, reward_type, reward_value) VALUES (%s, %s, %s, %s);",
            (code, activations, reward_type, value)
        )
    except Exception:
        await msg.reply(f"❌ Промокод <code>{code}</code> уже существует или произошла ошибка базы данных.")
        return

    await msg.reply(
        f"✅ <b>Промокод {code} успешно создан!</b>\n"
        f"👥 Активаций: <b>{activations}</b>\n"
        f"🎁 Награда: <b>{raw_type} (+{value})</b>"
    )

# ==================== 2. УДАЛЕНИЕ ПРОМОКОДА (АДМИН) ====================
@promos_router.message(Command("del_promo"))
async def cmd_del_promo(msg: types.Message, db):
    if not is_admin(msg):
        await msg.reply("❌ У вас нет прав для удаления промокодов!")
        return

    await ensure_promo_table(db)
    args = msg.text.split()
    if len(args) < 2:
        await msg.reply("❌ Использование: <code>/del_promo [код]</code>")
        return

    code = args[1].upper()
    await db.execute("DELETE FROM Promos WHERE code = %s;", (code,))
    await db.execute("DELETE FROM PromoActivations WHERE code = %s;", (code,))
    await msg.reply(f"🗑 Промокод <code>{code}</code> удален.")

# ==================== 3. СПИСОК / ИНФО О ПРОМОКОДАХ (АДМИН) ====================
@promos_router.message(Command("promo_info"))
async def cmd_promo_info(msg: types.Message, db):
    if not is_admin(msg):
        await msg.reply("❌ У вас нет прав для просмотра информации о промокодах!")
        return

    await ensure_promo_table(db)
    await db.execute("SELECT code, activations_left, reward_type, reward_value FROM Promos;")
    promos = await db.fetchall()

    if not promos:
        await msg.reply("📭 В базе данных пока нет активных промокодов.")
        return

    text = "📋 <b>Список активных промокодов:</b>\n\n"
    
    for p in promos:
        if isinstance(p, dict):
            code, left, rtype, rval = p.get("code"), p.get("activations_left"), p.get("reward_type"), p.get("reward_value")
        else:
            code, left, rtype, rval = p[0], p[1], p[2], p[3]
            
        text += f"🔑 <code>{code}</code>\n" \
                f"├ Осталось активаций: <b>{left}</b>\n" \
                f"└ Награда: <b>{rtype} (+{rval})</b>\n\n"

    await msg.reply(text)

# ==================== 4. АКТИВАЦИЯ ПРОМОКОДА (ВСЕ) ====================
@promos_router.message(F.text.lower().startswith("!промо") | F.text.lower().startswith("/promo"))
async def cmd_activate_promo(msg: types.Message, db):
    await ensure_promo_table(db)
    args = msg.text.split()
    
    if len(args) < 2:
        await msg.reply("❌ Использование: <code>!промо [код]</code> или <code>/promo [код]</code>")
        return

    code = args[1].upper()
    user_id = msg.from_user.id

    await db.execute("SELECT activations_left, reward_type, reward_value FROM Promos WHERE code = %s;", (code,))
    promo = await db.fetchone()

    if not promo:
        await msg.reply("❌ Такого промокода не существует или он был удален.")
        return

    if isinstance(promo, dict):
        left = promo.get("activations_left", 0)
        rtype = promo.get("reward_type")
        rval = promo.get("reward_value")
    else:
        left, rtype, rval = promo[0], promo[1], promo[2]

    if left <= 0:
        await msg.reply("❌ У этого промокода закончились активации.")
        return

    await db.execute("SELECT * FROM PromoActivations WHERE code = %s AND user_id = %s;", (code, user_id))
    activated = await db.fetchone()

    if activated:
        await msg.reply("❌ Вы уже активировали этот промокод!")
        return

    await db.execute("SELECT lab_id FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await db.fetchone()
    if not lab:
        await msg.reply("❌ У вас нет лаборатории! Напишите любое сообщение в чате, чтобы она создалась.")
        return

    await db.execute(f"UPDATE Lab SET {rtype} = {rtype} + %s WHERE lab_id = %s;", (rval, user_id))
    await db.execute("UPDATE Promos SET activations_left = activations_left - 1 WHERE code = %s;", (code,))
    await db.execute("INSERT INTO PromoActivations (code, user_id) VALUES (%s, %s);", (code, user_id))

    await msg.reply(f"🎉 <b>Промокод успешно активирован!</b>\n🎁 Вы получили награду: <b>+{rval}</b>")

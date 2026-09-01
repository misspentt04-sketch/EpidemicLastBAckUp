import math
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.text_decorations import html_decoration as hd

rebirth_router = Router()

def get_rebirth_cost(n: int) -> int:
    if n <= 1:
        return 5_000_000
    return 5_000_000 + (n - 1) * 10_000_000 + ((n - 1) * (n - 2) // 2) * 10_000_000

def generate_progress_bar(current: int, target: int, length: int = 15) -> str:
    if target <= 0:
        return "[███████████████] 100%"
    percent = min(1.0, max(0.0, current / target))
    filled_length = int(length * percent)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"[{bar}] {percent * 100:.1f}%"

@rebirth_router.message(Command("top_rb", "toprb"))
@rebirth_router.message(F.text.regexp(r"(?i)^(топ\s+(рб|перерождений|перерождения))$"))
async def cmd_top_rb(message: types.Message, db):
    query = """
        SELECT lab_id, lab_name, rebirth_level
        FROM Lab
        WHERE rebirth_level > 0
        ORDER BY rebirth_level DESC
        LIMIT 10;
    """

    await db.execute(query)
    rows = await db.fetchall()

    if not rows:
        return await message.answer("🔄 <b>ТОП ПО ПЕРЕРОЖДЕНИЯМ</b>\n\n<i>Пока никто не совершил перерождение.</i>", parse_mode="HTML")

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🔄 <b>ТОП ПО ПЕРЕРОЖДЕНИЯМ</b>\n"]

    for idx, row in enumerate(rows, 1):
        if isinstance(row, dict):
            user_id = row.get("lab_id")
            name = row.get("lab_name")
            rb_lvl = row.get("rebirth_level", 0) or 0
        else:
            user_id = row[0]
            name = row[1]
            rb_lvl = row[2] if len(row) > 2 and row[2] is not None else 0

        if not name:
            name = f"Лаборатория {user_id}"

        escaped_name = hd.quote(str(name))
        user_display = f'<a href="tg://openmessage?user_id={user_id}">{escaped_name}</a>'
        prefix = medals[idx - 1] if idx <= 3 else f"<b>{idx}.</b>"

        lines.append(f"{prefix} {user_display} — <code>{rb_lvl}</code> перерождение(й)")

    await message.answer("\n".join(lines), parse_mode="HTML")

@rebirth_router.message(Command("rebirth", "rb", "рб", "ребитх"))
@rebirth_router.message(F.text.in_({"/rebirth", "/rb", "/рб", "/ребитх"}))
async def cmd_rebirth(message: types.Message, db):
    user_id = message.from_user.id

    await db.execute(
        "SELECT bio_resource, rebirth_level FROM Lab WHERE lab_id = %s",
        (user_id,)
    )
    user_data = await db.fetchone()

    if not user_data:
        return await message.reply("❌ У вас еще нет Лаборатории!")

    bio_res = (user_data.get("bio_resource") if isinstance(user_data, dict) else user_data[0]) or 0
    rebirth_lvl = (user_data.get("rebirth_level") if isinstance(user_data, dict) else user_data[1]) or 0

    curr_ezha = rebirth_lvl * 10
    curr_disc = min(rebirth_lvl * 2.5, 10.0)

    next_lvl = rebirth_lvl + 1
    next_ezha = next_lvl * 10
    next_disc = min(next_lvl * 2.5, 10.0)

    cost = get_rebirth_cost(next_lvl)

    # Прогрессия стартовых бонусов
    start_exp = 1000 + (next_lvl - 1) * 1000
    start_bio = 15000 + (next_lvl - 1) * 10000

    await db.execute(
        "SELECT SUM(victim_bio_resource_earn) FROM Victims WHERE victims_owner_id = %s;",
        (user_id,)
    )
    res_tick = await db.fetchone()
    if isinstance(res_tick, dict):
        raw_tick = res_tick.get("SUM(victim_bio_resource_earn)") or 0
    elif isinstance(res_tick, tuple):
        raw_tick = res_tick[0] if res_tick[0] is not None else 0
    else:
        raw_tick = 0

    base_tick = float(raw_tick)

    single_tick_earn = base_tick * (1.0 + float(curr_ezha) / 100.0)
    daily_income = single_tick_earn * 2.0

    progress_bar = generate_progress_bar(bio_res, cost)
    needed = cost - bio_res

    if needed <= 0:
        days_left = "Готово к сбросу!"
    elif daily_income <= 0:
        days_left = "Нет жертв (доход 0/день)"
    else:
        days_left = f"~ {needed / daily_income:.1f} дн."

    info_text = (
        f"🔄 <b>Перерождение (Rebirth)</b>\n\n"
        f"📊 <b>Текущий уровень:</b> {rebirth_lvl}\n"
        f"⭐ <b>Текущие бонусы:</b>\n"
        f"  • Ежа с жертв: <b>+{curr_ezha}%</b>\n"
        f"  • Скидка на улучшения: <b>-{curr_disc}%</b>\n\n"
        f"🚀 <b>Следующий уровень (#{next_lvl}):</b>\n"
        f"  • Ежа с жертв: <b>+{next_ezha}%</b> (<i>+{next_ezha - curr_ezha}%</i>)\n"
        f"  • Скидка на улучшения: <b>-{next_disc}%</b> (<i>-{round(next_disc - curr_disc, 1)}%</i>)\n\n"
        f"🎯 <b>Цель:</b> {cost:,} биоресурсов\n"
        f"💰 <b>Накоплено:</b> {bio_res:,} / {cost:,}\n"
        f"<code>{progress_bar}</code>\n"
        f"⏳ <b>Доступно через:</b> {days_left}\n"
    )

    if bio_res < cost:
        return await message.reply(
            f"{info_text}\n❌ <i>Недостаточно биоресурсов для выполнения сброса.</i>",
            parse_mode="HTML"
        )

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить сброс", callback_data=f"confirm_rebirth:{user_id}:{next_lvl}")
    builder.button(text="❌ Отмена", callback_data=f"cancel_rebirth:{user_id}")
    builder.adjust(1)

    await message.reply(
        f"{info_text}\n"
        f"🎉 <b>Rebirth #{next_lvl} ДОСТУПЕН К АКТИВАЦИИ!</b>\n\n"
        f"⚠️ <b>ВНИМАНИЕ! БУДЕТ ВЫПОЛНЕН ПОЛНЫЙ СБРОС:</b>\n"
        f"❌ Биоресурсы (старт: {start_bio:,}) и Опыт (старт: {start_exp:,})\n"
        f"❌ Все патогены (до 4 шт.)\n"
        f"❌ Вся наука, заражаемость, иммунитет, летальность и СБ (до 1)\n"
        f"❌ Все ваши зараженные жертвы и кейсы\n\n"
        f"🦠 <i>Ваши болезни (кто заразил вас) останутся нетронутыми.</i>\n\n"
        f"Списать <b>{cost:,}</b> биоресурсов и сбросить прогресс?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@rebirth_router.callback_query(F.data.startswith("confirm_rebirth:"))
async def process_rebirth_confirm(callback: types.CallbackQuery, db):
    await callback.answer()

    _, owner_id, target_lvl = callback.data.split(":")
    owner_id = int(owner_id)
    target_lvl = int(target_lvl)

    if callback.from_user.id != owner_id:
        return await callback.answer("❌ Это не ваше меню!", show_alert=True)

    cost = get_rebirth_cost(target_lvl)

    await db.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (owner_id,))
    user_data = await db.fetchone()

    if isinstance(user_data, dict):
        bio_res = user_data.get("bio_resource") or 0
    elif isinstance(user_data, (list, tuple)):
        bio_res = user_data[0] or 0
    else:
        bio_res = 0

    if not user_data or bio_res < cost:
        return await callback.message.edit_text("❌ Недостаточно биоресурсов для выполнения Rebirth!")

    # Динамический расчет бонусов
    start_exp = 1000 + (target_lvl - 1) * 1000
    start_bio = 15000 + (target_lvl - 1) * 10000

    # Удаление зараженных жертв
    await db.execute("DELETE FROM Victims WHERE victims_owner_id = %s;", (owner_id,))

    # Сброс лаборатории с новыми стартовыми ресурсами
    query_update = """
        UPDATE Lab
        SET bio_resource = %s,
            bio_experience = %s,
            pathogens = 4,
            ready_pathogens = 4,
            science = 1,
            infect = 1,
            immunity = 1,
            lethality = 1,
            security_service = 1,
            epicoins = 0,
            case1 = 0,
            case2 = 0,
            rebirth_level = %s
        WHERE lab_id = %s;
    """
    await db.execute(query_update, (start_bio, start_exp, target_lvl, owner_id))

    await callback.message.edit_text(
        f"🎉 <b>ПОЗДРАВЛЯЕМ С REBIRTH #{target_lvl}!</b>\n\n"
        f"🔄 Все показатели Лаборатории и жертвы сброшены.\n"
        f"🎁 Стартовые ресурсы: <b>{start_bio:,}</b> биоресурсов и <b>{start_exp:,}</b> опыта.\n"
        f"✨ Новые перманентные бонусы активированы!",
        parse_mode="HTML"
    )

@rebirth_router.callback_query(F.data.startswith("cancel_rebirth:"))
async def process_rebirth_cancel(callback: types.CallbackQuery):
    await callback.answer()
    _, owner_id = callback.data.split(":")
    if callback.from_user.id != int(owner_id):
        return await callback.answer("❌ Это не ваше меню!", show_alert=True)

    await callback.message.edit_text("❌ Перерождение отменено. Ваша Лаборатория в безопасности.")

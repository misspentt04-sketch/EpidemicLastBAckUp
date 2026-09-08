import time
from datetime import datetime, timezone
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.pool import Pool
from redis.asyncio import Redis

router = Router()

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С УЧЕНИКОМ =====

async def get_student_lab(pool: Pool, user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM StudentLab WHERE lab_id = %s", (user_id,))
            return await cur.fetchone()

async def create_student_lab(pool: Pool, user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO StudentLab (lab_id, is_active, created_at) VALUES (%s, FALSE, NOW())",
                (user_id,)
            )

async def get_student_income(user_id: int, lab: dict, pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            owner_resources = row[0] if row else 0

    total_skills = (
        lab.get('infect', 0) +
        lab.get('immunity', 0) +
        lab.get('lethality', 0) +
        lab.get('security_service', 0) +
        lab.get('science', 0) +
        lab.get('pathogens', 0)
    )

    income = owner_resources * 0.001 * (1 + 0.05 * total_skills)
    return int(income)

async def get_mission_progress(pool: Pool, user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT COUNT(*) as total, SUM(completed) as done
                FROM StudentMissionProgress
                WHERE user_id = %s
            """, (user_id,))
            row = await cur.fetchone()
            total = row[0] if row else 0
            done = row[1] if row else 0
            return total, done

async def get_all_missions(pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, question, hint FROM StudentMissions WHERE is_active = TRUE")
            return await cur.fetchall()

# ===== ОБРАБОТЧИК ДЛЯ МИССИЙ =====
@router.callback_query(F.data == "student_missions")
async def student_missions(call: CallbackQuery, pool: Pool):
    user_id = call.from_user.id

    lab = await get_student_lab(pool, user_id)
    if lab:
        if isinstance(lab, dict):
            is_active = lab.get('is_active', False)
        else:
            is_active = lab[1] if len(lab) > 1 else False
        if is_active:
            await call.answer("✅ Лаборатория уже активирована!", show_alert=True)
            return

    missions = await get_all_missions(pool)
    progress = await get_mission_progress(pool, user_id)
    total, done = progress

    text = f"📋 <b>Миссии для активации</b>\n\n"
    text += f"Выполнено: <b>{done}/{total}</b>\n\n"

    for mission in missions:
        if isinstance(mission, dict):
            mid = mission.get('id')
            name = mission.get('name')
        else:
            mid = mission[0]
            name = mission[1]
        text += f"• <b>{name}</b> (ID: {mid})\n"

    text += "\n💡 Чтобы ответить: <code>/ученик ответ &lt;id&gt; &lt;текст&gt;</code>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="student_missions")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="student_back")]
    ])

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "student_refresh")
async def student_refresh(call: CallbackQuery, pool: Pool):
    await call.answer("🔄 Обновляю...")
    await cmd_student_lab(call.message, pool)

@router.callback_query(F.data == "student_back")
async def student_back(call: CallbackQuery, pool: Pool):
    await call.answer()
    await cmd_student_lab(call.message, pool)

# ===== КОМАНДА /LAB_УЧ =====
@router.message(F.text.lower() == "/lab_уч")
async def cmd_student_lab(msg: Message, pool: Pool):
    user_id = msg.from_user.id

    lab = await get_student_lab(pool, user_id)
    if not lab:
        await create_student_lab(pool, user_id)
        lab = await get_student_lab(pool, user_id)

    if isinstance(lab, dict):
        is_active = lab.get('is_active', False)
        infect = lab.get('infect', 0)
        immunity = lab.get('immunity', 0)
        lethality = lab.get('lethality', 0)
        security = lab.get('security_service', 0)
        science = lab.get('science', 0)
        pathogens = lab.get('pathogens', 0)
        total_earned = lab.get('total_earned', 0)
        total_skills = infect + immunity + lethality + security + science + pathogens
    else:
        is_active = lab[1] if len(lab) > 1 else False
        infect = lab[2] if len(lab) > 2 else 0
        immunity = lab[3] if len(lab) > 3 else 0
        lethality = lab[4] if len(lab) > 4 else 0
        security = lab[5] if len(lab) > 5 else 0
        science = lab[6] if len(lab) > 6 else 0
        pathogens = lab[7] if len(lab) > 7 else 0
        total_earned = lab[10] if len(lab) > 10 else 0
        total_skills = infect + immunity + lethality + security + science + pathogens

    if not is_active:
        total, done = await get_mission_progress(pool, user_id)
        text = (
            f"🧪 <b>Лаборатория ученика</b>\n\n"
            f"📊 Статус: <b>🔒 НЕ АКТИВИРОВАНА</b>\n"
            f"📋 Миссии: <b>{done}/{total}</b> выполнено\n"
            f"💡 Выполните все миссии через <code>/ученик миссии</code>\n"
            f"чтобы активировать лабораторию ученика!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список миссий", callback_data="student_missions")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="student_refresh")]
        ])
        await msg.reply(text, reply_markup=kb, parse_mode="HTML")
        return

    income = await get_student_income(user_id, lab, pool)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            owner_resources = row[0] if row else 0

    total, done = await get_mission_progress(pool, user_id)

    text = (
        f"🧪 <b>Лаборатория ученика</b>\n\n"
        f"📊 Статус: <b>✅ АКТИВНА</b>\n"
        f"🧬 Ресурсы владельца: <b>{owner_resources:,}</b>\n"
        f"📈 Доход ученика: <b>{income:,} 🧬/10 мин</b>\n"
        f"💰 Всего заработано: <b>{total_earned:,}</b>\n\n"
        f"🧮 <b>Навыки ученика:</b>\n"
        f"├ 🎯 Заразность: <b>{infect}</b>\n"
        f"├ 🛡 Иммунитет: <b>{immunity}</b>\n"
        f"├ ☠️ Летальность: <b>{lethality}</b>\n"
        f"├ 🔒 Безопасность: <b>{security}</b>\n"
        f"├ 🧬 Патогены: <b>{pathogens}</b>\n"
        f"└ 🧪 Разработка: <b>{science}</b>\n\n"
        f"📊 Сумма навыков: <b>{total_skills}</b>\n"
        f"💰 Доход = 0.1% × (1 + 5% × {total_skills}) = <b>{income/owner_resources*100:.2f}%</b> от ресурсов владельца\n\n"
        f"📋 Миссии выполнено: <b>{done}/{total}</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 +1 ЗЗ", callback_data="student_upgrade:infect"),
            InlineKeyboardButton(text="🛡 +1 Иммун", callback_data="student_upgrade:immunity"),
            InlineKeyboardButton(text="☠️ +1 Летал", callback_data="student_upgrade:lethality")
        ],
        [
            InlineKeyboardButton(text="🔒 +1 СБ", callback_data="student_upgrade:security_service"),
            InlineKeyboardButton(text="🧬 +1 Патоген", callback_data="student_upgrade:pathogens"),
            InlineKeyboardButton(text="🧪 +1 Разраб", callback_data="student_upgrade:science")
        ],
        [
            InlineKeyboardButton(text="📋 Миссии", callback_data="student_missions"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="student_refresh")
        ]
    ])

    await msg.reply(text, reply_markup=kb, parse_mode="HTML")

# ===== ПРОКАЧКА УЧЕНИКА (КНОПКИ) =====
@router.callback_query(F.data.startswith("student_upgrade:"))
async def student_upgrade(call: CallbackQuery, pool: Pool, repo_biowar):
    user_id = call.from_user.id
    skill = call.data.split(":")[1]

    lab = await get_student_lab(pool, user_id)
    if not lab:
        await call.answer("❌ У вас нет лаборатории ученика!", show_alert=True)
        return

    if isinstance(lab, dict):
        current_lvl = lab.get(skill, 0)
        is_active = lab.get('is_active', False)
    else:
        idx = {"infect": 2, "immunity": 3, "lethality": 4, "security_service": 5, "science": 6, "pathogens": 7}
        current_lvl = lab[idx.get(skill, 2)] if idx.get(skill, 2) < len(lab) else 0
        is_active = lab[1] if len(lab) > 1 else False

    if not is_active:
        await call.answer("❌ Лаборатория не активирована!", show_alert=True)
        return

    from core import func
    from core.data.tricks.tricks_biowar import tricks_biowar

    to_lvl = current_lvl + 1

    # Считаем цену по формуле заразности
    price = int(func.lvl_up_calc(skill, current_lvl, to_lvl))

    # Проверяем ресурсы
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            owner_resources = row[0] if row else 0

    if owner_resources < price:
        await call.answer(f"❌ Недостаточно ресурсов! Нужно {price:,} 🧬", show_alert=True)
        return

    # Списываем ресурсы
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s",
                (price, user_id)
            )
            await cur.execute(
                f"UPDATE StudentLab SET {skill} = {skill} + 1 WHERE lab_id = %s",
                (user_id,)
            )

    await call.answer(f"✅ {skill} повышен до {to_lvl}! -{price:,} 🧬", show_alert=False)
    await cmd_student_lab(call.message, pool)

# ===== КОМАНДА /УЧЕНИК ОТВЕТ =====
@router.message(F.text.lower().startswith("/ученик ответ"))
async def student_answer(msg: Message, pool: Pool):
    user_id = msg.from_user.id
    parts = msg.text.split(maxsplit=2)

    if len(parts) < 3:
        await msg.reply("❌ Формат: <code>/ученик ответ &lt;id&gt; &lt;текст&gt;</code>", parse_mode="HTML")
        return

    try:
        mission_id = int(parts[1])
        answer = parts[2].strip().lower()
    except:
        await msg.reply("❌ Укажите ID миссии и ответ!")
        return

    lab = await get_student_lab(pool, user_id)
    if lab:
        if isinstance(lab, dict):
            is_active = lab.get('is_active', False)
        else:
            is_active = lab[1] if len(lab) > 1 else False
        if is_active:
            await msg.reply("✅ Лаборатория уже активирована!")
            return

    # Проверяем миссию
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, answer, name FROM StudentMissions WHERE id = %s AND is_active = TRUE",
                (mission_id,)
            )
            mission = await cur.fetchone()

    if not mission:
        await msg.reply("❌ Миссия не найдена!")
        return

    if isinstance(mission, dict):
        correct_answer = mission.get('answer', '').lower()
        mission_name = mission.get('name', '')
    else:
        correct_answer = mission[1].lower() if len(mission) > 1 else ''
        mission_name = mission[2] if len(mission) > 2 else ''

    if answer == correct_answer:
        # Записываем прогресс
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO StudentMissionProgress (user_id, mission_id, completed, completed_at) VALUES (%s, %s, TRUE, NOW()) "
                    "ON DUPLICATE KEY UPDATE completed = TRUE, completed_at = NOW()",
                    (user_id, mission_id)
                )

        await msg.reply(f"✅ Правильно! Миссия «{mission_name}» выполнена!")

        # Проверяем, все ли миссии выполнены
        total, done = await get_mission_progress(pool, user_id)
        all_missions = await get_all_missions(pool)

        if done >= len(all_missions):
            # Активируем лабораторию
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "UPDATE StudentLab SET is_active = TRUE, last_income_time = %s WHERE lab_id = %s",
                        (int(time.time()), user_id)
                    )
            await msg.reply(
                "🎉 <b>Лаборатория ученика активирована!</b>\n\n"
                "Теперь ученик приносит доход каждый час!\n"
                "Используйте <code>/lab_уч</code> для управления.",
                parse_mode="HTML"
            )
    else:
        await msg.reply(f"❌ Неправильно! Попробуйте ещё раз.\n💡 Подсказка: {mission[2] if len(mission) > 2 else 'нет подсказки'}")

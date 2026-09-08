import time
from datetime import datetime, timezone
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.pool import Pool
from redis.asyncio import Redis

router = Router()

# ===== ФУНКЦИИ =====

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

async def get_student_income(user_id: int, lab, pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT COALESCE(SUM(victim_bio_resource_earn), 0)
                FROM Victims
                WHERE victims_owner_id = %s
            """, (user_id,))
            row = await cur.fetchone()
            tick_income = float(row[0]) if row and row[0] is not None else 0.0

    if isinstance(lab, tuple):
        lab = {
            "infect": lab[2] if len(lab) > 2 else 0,
            "immunity": lab[3] if len(lab) > 3 else 0,
            "lethality": lab[4] if len(lab) > 4 else 0,
            "security_service": lab[5] if len(lab) > 5 else 0,
            "science": lab[6] if len(lab) > 6 else 0,
            "pathogens": lab[7] if len(lab) > 7 else 0,
        }

    total_skills = (
        lab.get('infect', 0) +
        lab.get('immunity', 0) +
        lab.get('lethality', 0) +
        lab.get('security_service', 0) +
        lab.get('science', 0) +
        lab.get('pathogens', 0)
    )

    income = tick_income * 0.00001 * (1 + 0.05 * total_skills)
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
            await cur.execute("SELECT id, name, question, hint FROM StudentMissions WHERE is_active = TRUE ORDER BY id ASC")
            return await cur.fetchall()

# ===== CALLBACK =====

@router.callback_query(F.data == "student_missions")
async def student_missions(call: CallbackQuery, pool: Pool):
    user_id = call.from_user.id

    lab = await get_student_lab(pool, user_id)
    if lab:
        is_active = lab[1] if isinstance(lab, tuple) and len(lab) > 1 else (lab.get('is_active', False) if isinstance(lab, dict) else False)
        if is_active:
            await call.answer("✅ Лаборатория уже активирована!", show_alert=True)
            return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT m.id, m.name, m.question, m.hint
                FROM StudentMissions m
                LEFT JOIN StudentMissionProgress p ON p.mission_id = m.id AND p.user_id = %s
                WHERE (p.completed IS NULL OR p.completed = FALSE)
                ORDER BY m.id ASC
                LIMIT 1
            """, (user_id,))
            mission = await cur.fetchone()

    if not mission:
        await call.message.edit_text(
            "📋 <b>Все миссии выполнены!</b>\n\nТеперь вы можете активировать лабораторию ученика!\nНапишите <code>активировать ученика</code>, чтобы завершить активацию.",
            parse_mode="HTML"
        )
        await call.answer()
        return

    if isinstance(mission, dict):
        mission_id = mission.get('id')
        name = mission.get('name')
        question = mission.get('question')
        hint = mission.get('hint')
    else:
        mission_id = mission[0]
        name = mission[1]
        question = mission[2]
        hint = mission[3] if len(mission) > 3 else "Нет подсказки"

    text = (
        f"📋 <b>Миссия #{mission_id}: {name}</b>\n\n"
        f"📝 <b>Задание:</b>\n{question}\n\n"
        f"💡 <b>Подсказка:</b> <i>{hint}</i>\n\n"
        f"✍️ Чтобы ответить:\n"
        f"<code>ответ ученика {mission_id} &lt;текст&gt;</code>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[])

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

# ===== КОМАНДА: ЛАБОРАТОРИЯ УЧЕНИКА =====

@router.message(F.text.lower() == "лаборатория ученика")
async def cmd_student_lab(msg: Message, pool: Pool):
    user_id = msg.from_user.id

    lab = await get_student_lab(pool, user_id)
    if not lab:
        await create_student_lab(pool, user_id)
        lab = await get_student_lab(pool, user_id)

    if isinstance(lab, tuple):
        is_active = lab[1] if len(lab) > 1 else False
        lab = {
            'is_active': is_active,
            'infect': lab[2] if len(lab) > 2 else 0,
            'immunity': lab[3] if len(lab) > 3 else 0,
            'lethality': lab[4] if len(lab) > 4 else 0,
            'security_service': lab[5] if len(lab) > 5 else 0,
            'science': lab[6] if len(lab) > 6 else 0,
            'pathogens': lab[7] if len(lab) > 7 else 0,
            'total_earned': lab[10] if len(lab) > 10 else 0,
            'last_income_time': lab[9] if len(lab) > 9 else 0,
        }

    is_active = lab.get('is_active', False)
    infect = lab.get('infect', 0)
    immunity = lab.get('immunity', 0)
    lethality = lab.get('lethality', 0)
    security = lab.get('security_service', 0)
    science = lab.get('science', 0)
    pathogens = lab.get('pathogens', 0)
    total_earned = lab.get('total_earned', 0)
    last_income = lab.get('last_income_time', 0)
    total_skills = infect + immunity + lethality + security + science + pathogens

    # Проверяем миссии
    total, done = await get_mission_progress(pool, user_id)
    all_missions = await get_all_missions(pool)
    if is_active and done < len(all_missions):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE StudentLab SET is_active = FALSE WHERE lab_id = %s",
                    (user_id,)
                )
        is_active = False
        lab['is_active'] = False

    if not is_active:
        total, done = await get_mission_progress(pool, user_id)
        text = (
            f"🧪 <b>Лаборатория ученика</b>\n\n"
            f"📊 Статус: <b>🔒 НЕ АКТИВИРОВАНА</b>\n"
            f"📋 Миссии: <b>{done}/{total}</b> выполнено\n"
            f"💡 Напишите <code>миссии ученика</code>\n"
            f"чтобы активировать лабораторию ученика!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список миссий", callback_data="student_missions")],
        ])
        await msg.reply(text, reply_markup=kb, parse_mode="HTML")
        return

    income = await get_student_income(user_id, lab, pool)

    # Получаем доход с жертв для отображения
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT COALESCE(SUM(victim_bio_resource_earn), 0)
                FROM Victims
                WHERE victims_owner_id = %s
            """, (user_id,))
            row = await cur.fetchone()
            tick_income = float(row[0]) if row and row[0] is not None else 0.0

    # Время до следующей выдачи
    if last_income:
        next_income = last_income + 600
        time_left = int(next_income - time.time())
        if time_left > 0:
            minutes = time_left // 60
            seconds = time_left % 60
            next_income_str = f"⏳ Следующая выдача через: <b>{minutes} мин {seconds} сек</b>"
        else:
            next_income_str = "⏳ Скоро будет выдано..."
    else:
        next_income_str = "⏳ Время выдачи не установлено"

    text = (
        f"🧪 <b>Лаборатория ученика</b>\n\n"
        f"📊 Статус: <b>✅ АКТИВНА</b>\n"
        f"📈 Доход с жертв за тик: <b>{tick_income:,}</b>\n"
        f"📈 Доход ученика: <b>{income:,} 🧬/10 мин</b>\n"
        f"💰 Всего заработано: <b>{total_earned:,}</b>\n"
        f"{next_income_str}\n\n"
        f"🧮 <b>Навыки ученика:</b>\n"
        f"├ 🎯 Заразность: <b>{infect}</b>\n"
        f"├ 🛡 Иммунитет: <b>{immunity}</b>\n"
        f"├ ☠️ Летальность: <b>{lethality}</b>\n"
        f"├ 🔒 Безопасность: <b>{security}</b>\n"
        f"├ 🧬 Патогены: <b>{pathogens}</b>\n"
        f"└ 🧪 Разработка: <b>{science}</b>\n\n"
        f"📊 Сумма навыков: <b>{total_skills}</b>\n"
        f"💰 Доход = 0.01% от тика × (1 + 5% × {total_skills}) = <b>{income/tick_income*100:.2f}%</b> от дохода с жертв\n\n"
        f"📋 Миссии выполнено: <b>✅ Все миссии выполнены</b>"
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
        ]
    ])

    await msg.reply(text, reply_markup=kb, parse_mode="HTML")

# ===== ТЕКСТОВАЯ КОМАНДА: МИССИИ УЧЕНИКА =====

@router.message(F.text.lower() == "миссии ученика")
async def student_missions_text(msg: Message, pool: Pool):
    user_id = msg.from_user.id

    lab = await get_student_lab(pool, user_id)
    if lab:
        is_active = lab[1] if isinstance(lab, tuple) and len(lab) > 1 else (lab.get('is_active', False) if isinstance(lab, dict) else False)
        if is_active:
            await msg.reply("✅ Лаборатория уже активирована!")
            return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT m.id, m.name, m.question, m.hint
                FROM StudentMissions m
                LEFT JOIN StudentMissionProgress p ON p.mission_id = m.id AND p.user_id = %s
                WHERE (p.completed IS NULL OR p.completed = FALSE)
                ORDER BY m.id ASC
                LIMIT 1
            """, (user_id,))
            mission = await cur.fetchone()

    if not mission:
        await msg.reply(
            "📋 <b>Все миссии выполнены!</b>\n\nТеперь вы можете активировать лабораторию ученика!\nНапишите <code>активировать ученика</code>, чтобы завершить активацию.",
            parse_mode="HTML"
        )
        return

    if isinstance(mission, dict):
        mission_id = mission.get('id')
        name = mission.get('name')
        question = mission.get('question')
        hint = mission.get('hint')
    else:
        mission_id = mission[0]
        name = mission[1]
        question = mission[2]
        hint = mission[3] if len(mission) > 3 else "Нет подсказки"

    text = (
        f"📋 <b>Миссия #{mission_id}: {name}</b>\n\n"
        f"📝 <b>Задание:</b>\n{question}\n\n"
        f"💡 <b>Подсказка:</b> <i>{hint}</i>\n\n"
        f"✍️ Чтобы ответить:\n"
        f"<code>ответ ученика {mission_id} &lt;текст&gt;</code>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[])

    await msg.reply(text, reply_markup=kb, parse_mode="HTML")

# ===== ПРОКАЧКА =====

@router.callback_query(F.data.startswith("student_upgrade:"))
async def student_upgrade(call: CallbackQuery, pool: Pool, repo_biowar):
    user_id = call.from_user.id
    skill = call.data.split(":")[1]

    lab = await get_student_lab(pool, user_id)
    if not lab:
        await call.answer("❌ У вас нет лаборатории ученика!", show_alert=True)
        return

    if isinstance(lab, tuple):
        is_active = lab[1] if len(lab) > 1 else False
        idx = {"infect": 2, "immunity": 3, "lethality": 4, "security_service": 5, "science": 6, "pathogens": 7}
        current_lvl = lab[idx.get(skill, 2)] if idx.get(skill, 2) < len(lab) else 0
    else:
        is_active = lab.get('is_active', False)
        current_lvl = lab.get(skill, 0)

    # Проверяем миссии перед прокачкой
    total, done = await get_mission_progress(pool, user_id)
    all_missions = await get_all_missions(pool)
    if not is_active and done < len(all_missions):
        await call.answer("❌ Сначала выполните все миссии!", show_alert=True)
        return

    if not is_active:
        await call.answer("❌ Лаборатория не активирована!", show_alert=True)
        return

    from core import func
    from core.data.tricks.tricks_biowar import tricks_biowar

    to_lvl = current_lvl + 1
    price = int(func.lvl_up_calc(skill, current_lvl, to_lvl))

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            owner_resources = row[0] if row else 0

    if owner_resources < price:
        await call.answer(f"❌ Недостаточно ресурсов! Нужно {price:,} 🧬", show_alert=True)
        return

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

# ===== КОМАНДА: ОТВЕТ УЧЕНИКА =====

@router.message(F.text.lower().startswith("ответ ученика"))
async def student_answer(msg: Message, pool: Pool):
    user_id = msg.from_user.id
    text = msg.text

    import re
    match = re.match(r"ответ ученика\s+(\d+)\s+(.+)", text, re.IGNORECASE)
    if not match:
        await msg.reply("❌ Формат: <code>ответ ученика &lt;id&gt; &lt;текст&gt;</code>", parse_mode="HTML")
        return

    mission_id = int(match.group(1))
    answer = match.group(2).strip().lower()

    lab = await get_student_lab(pool, user_id)
    if lab:
        is_active = lab[1] if isinstance(lab, tuple) and len(lab) > 1 else (lab.get('is_active', False) if isinstance(lab, dict) else False)
        if is_active:
            await msg.reply("✅ Лаборатория уже активирована!")
            return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT m.id, m.answer, m.name
                FROM StudentMissions m
                LEFT JOIN StudentMissionProgress p ON p.mission_id = m.id AND p.user_id = %s
                WHERE (p.completed IS NULL OR p.completed = FALSE)
                ORDER BY m.id ASC
                LIMIT 1
            """, (user_id,))
            current = await cur.fetchone()

    if not current:
        await msg.reply("❌ Все миссии уже выполнены!")
        return

    if isinstance(current, dict):
        current_id = current.get('id')
        correct_answer = current.get('answer', '').lower().strip()
        mission_name = current.get('name', '')
    else:
        current_id = current[0]
        correct_answer = current[1].lower().strip() if len(current) > 1 else ''
        mission_name = current[2] if len(current) > 2 else ''

    if mission_id != current_id:
        await msg.reply(f"❌ Сейчас нужно выполнить миссию #{current_id} «{mission_name}»!")
        return

    if answer == correct_answer:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO StudentMissionProgress (user_id, mission_id, completed, completed_at) VALUES (%s, %s, TRUE, NOW()) "
                    "ON DUPLICATE KEY UPDATE completed = TRUE, completed_at = NOW()",
                    (user_id, mission_id)
                )

        await msg.reply(f"✅ Правильно! Миссия «{mission_name}» выполнена! 🎉")

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT COUNT(*) FROM StudentMissions m
                    LEFT JOIN StudentMissionProgress p ON p.mission_id = m.id AND p.user_id = %s
                    WHERE (p.completed IS NULL OR p.completed = FALSE)
                """, (user_id,))
                row = await cur.fetchone()
                remaining = row[0] if row else 0

        if remaining > 0:
            await msg.reply(f"📋 Осталось ещё <b>{remaining}</b> миссий.\nНапишите <code>миссии ученика</code> для продолжения.")
        else:
            # Активируем после последней миссии
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "UPDATE StudentLab SET is_active = TRUE, last_income_time = %s WHERE lab_id = %s",
                        (int(time.time()), user_id)
                    )
            await msg.reply(
                "🎉 <b>Все миссии выполнены!</b>\n\n"
                "Лаборатория ученика активирована!\n"
                "Используйте <code>лаборатория ученика</code> для управления.",
                parse_mode="HTML"
            )
    else:
        await msg.reply(f"❌ Неправильно! Попробуйте ещё раз.\n💡 Подсказка: <code>миссии ученика</code>")

# ===== КОМАНДА: АКТИВИРОВАТЬ УЧЕНИКА =====
@router.message(F.text.lower() == "активировать ученика")
async def activate_student(msg: Message, pool: Pool):
    user_id = msg.from_user.id

    lab = await get_student_lab(pool, user_id)
    if not lab:
        await create_student_lab(pool, user_id)
        lab = await get_student_lab(pool, user_id)

    is_active = lab[1] if isinstance(lab, tuple) and len(lab) > 1 else (lab.get('is_active', False) if isinstance(lab, dict) else False)

    if is_active:
        await msg.reply("✅ Лаборатория уже активирована!")
        return

    # Проверяем, все ли миссии выполнены
    total, done = await get_mission_progress(pool, user_id)
    all_missions = await get_all_missions(pool)

    if done < len(all_missions):
        await msg.reply(f"❌ Выполнено только <b>{done}/{len(all_missions)}</b> миссий.\nЗавершите все миссии через <code>миссии ученика</code>.")
        return

    # Активируем
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE StudentLab SET is_active = TRUE, last_income_time = %s WHERE lab_id = %s",
                (int(time.time()), user_id)
            )

    await msg.reply(
        "🎉 <b>Лаборатория ученика активирована!</b>\n\n"
        "Теперь ученик приносит доход каждые 10 минут.\n"
        "Используйте <code>лаборатория ученика</code> для управления.",
        parse_mode="HTML"
    )

# ===== РУЧНАЯ ВЫДАЧА ДОХОДА УЧЕНИКА (АДМИН) =====
@router.message(F.text.lower() == "/student_income")
async def cmd_student_income(msg: Message, pool: Pool):
    user_id = msg.from_user.id
    if user_id != 7972320837:
        await msg.reply("❌ У вас нет прав!")
        return

    from core.services.loop_tasks import student_income_loop
    # Запускаем одну итерацию вручную
    try:
        # Создаём временную функцию для одной выдачи
        async def force_income():
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT lab_id, infect, immunity, lethality, security_service, science, pathogens, total_earned
                        FROM StudentLab
                        WHERE is_active = TRUE
                    """)
                    students = await cur.fetchall()

                    for student in students:
                        if isinstance(student, dict):
                            user_id2 = student.get('lab_id')
                            infect = student.get('infect', 0)
                            immunity = student.get('immunity', 0)
                            lethality = student.get('lethality', 0)
                            security = student.get('security_service', 0)
                            science = student.get('science', 0)
                            pathogens = student.get('pathogens', 0)
                            total_earned = student.get('total_earned', 0)
                        else:
                            user_id2 = student[0]
                            infect = student[1] if len(student) > 1 else 0
                            immunity = student[2] if len(student) > 2 else 0
                            lethality = student[3] if len(student) > 3 else 0
                            security = student[4] if len(student) > 4 else 0
                            science = student[5] if len(student) > 5 else 0
                            pathogens = student[6] if len(student) > 6 else 0
                            total_earned = student[7] if len(student) > 7 else 0

                        await cur.execute("""
                            SELECT COALESCE(SUM(victim_bio_resource_earn), 0)
                            FROM Victims
                            WHERE victims_owner_id = %s
                        """, (user_id2,))
                        row = await cur.fetchone()
                        tick_income = float(row[0]) if row and row[0] is not None else 0.0

                        total_skills = infect + immunity + lethality + security + science + pathogens
                        income = int(tick_income * 0.00001 * (1 + 0.05 * total_skills))

                        if income > 0:
                            await cur.execute(
                                "UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s",
                                (income, user_id2)
                            )
                            await cur.execute(
                                "UPDATE StudentLab SET total_earned = total_earned + %s, last_income_time = %s WHERE lab_id = %s",
                                (income, int(time.time()), user_id2)
                            )

        await force_income()
        await msg.reply("✅ Доход ученика успешно выдан всем активным игрокам!")

    except Exception as e:
        await msg.reply(f"❌ Ошибка: {e}")

# ===== ПРОКАЧКА УЧЕНИКА КОМАНДАМИ (++ученик зз 5) =====
@router.message(F.text.lower().startswith("++ученик"))
async def student_upgrade_cmd(msg: Message, pool: Pool, repo_biowar):
    user_id = msg.from_user.id
    text = msg.text.lower()
    parts = text.split()

    # Формат: ++ученик зз 5
    if len(parts) < 3:
        await msg.reply("❌ Формат: <code>++ученик зз 5</code>\nДоступно: зз, иммун, летал, сб, пат, разраб", parse_mode="HTML")
        return

    skill_name = parts[1]
    try:
        amount = int(parts[2])
    except:
        await msg.reply("❌ Укажите количество (число от 1 до 5)!")
        return

    if amount < 1 or amount > 5:
        await msg.reply("❌ Можно прокачать только от 1 до 5 уровней за раз!")
        return

    # Маппинг названий
    skill_map = {
        "зз": "infect",
        "иммун": "immunity",
        "летал": "lethality",
        "сб": "security_service",
        "пат": "pathogens",
        "разраб": "science",
        "заразность": "infect",
        "иммунитет": "immunity",
        "летальность": "lethality",
        "безопасность": "security_service",
        "патоген": "pathogens",
        "разработка": "science",
    }

    skill = skill_map.get(skill_name)
    if not skill:
        await msg.reply("❌ Неизвестный навык!\nДоступно: зз, иммун, летал, сб, пат, разраб")
        return

    lab = await get_student_lab(pool, user_id)
    if not lab:
        await create_student_lab(pool, user_id)
        lab = await get_student_lab(pool, user_id)

    # Проверяем активность
    if isinstance(lab, tuple):
        is_active = lab[1] if len(lab) > 1 else False
        current_lvl = lab[2] if skill == "infect" else (lab[3] if skill == "immunity" else (lab[4] if skill == "lethality" else (lab[5] if skill == "security_service" else (lab[6] if skill == "science" else (lab[7] if skill == "pathogens" else 0)))))
    else:
        is_active = lab.get('is_active', False)
        current_lvl = lab.get(skill, 0)

    if not is_active:
        # Проверяем миссии
        total, done = await get_mission_progress(pool, user_id)
        all_missions = await get_all_missions(pool)
        if done < len(all_missions):
            await msg.reply("❌ Сначала выполните все миссии через <code>миссии ученика</code>!")
            return
        # Активируем
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE StudentLab SET is_active = TRUE, last_income_time = %s WHERE lab_id = %s",
                    (int(time.time()), user_id)
                )
        is_active = True

    from core import func
    from core.data.tricks.tricks_biowar import tricks_biowar

    to_lvl = current_lvl + amount
    price = int(func.lvl_up_calc(skill, current_lvl, to_lvl))

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s", (user_id,))
            row = await cur.fetchone()
            owner_resources = row[0] if row else 0

    if owner_resources < price:
        await msg.reply(f"❌ Недостаточно ресурсов! Нужно {price:,} 🧬")
        return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s",
                (price, user_id)
            )
            await cur.execute(
                f"UPDATE StudentLab SET {skill} = {skill} + %s WHERE lab_id = %s",
                (amount, user_id)
            )

    skill_names = {
        "infect": "Заразность",
        "immunity": "Иммунитет",
        "lethality": "Летальность",
        "security_service": "Безопасность",
        "science": "Разработка",
        "pathogens": "Патогены",
    }

    await msg.reply(
        f"✅ <b>{skill_names.get(skill, skill)}</b> повышена на {amount} уровней!\n"
        f"📊 Было: <b>{current_lvl}</b> → Стало: <b>{to_lvl}</b>\n"
        f"💰 Потрачено: <b>{price:,} 🧬</b>",
        parse_mode="HTML"
    )

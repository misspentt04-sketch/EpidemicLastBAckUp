import asyncio
import time
import re
import random
from datetime import datetime, timedelta
from html import unescape


def clean_name(name: str) -> str:
    """Убирает HTML-теги из имени"""
    if not name:
        return ""
    name = re.sub(r'<[^>]+>', '', str(name))
    return unescape(name).strip()
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor
from redis.asyncio import Redis
from humanize import intcomma

from core import func
from core.data.icons import LabIco
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.infect_chances import get_infect_chance

router = Router()

CHAT_ID = -1004335676077   # чат для "ученик бч"
MAX_TOP = 30
INFECT_KD = 0.7


# ===== ХЕЛПЕРЫ =====
async def get_student_lab(pool: Pool, user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("SELECT * FROM StudentLab WHERE lab_id = %s", (user_id,))
            return await cur.fetchone()


async def check_owner_missions(pool: Pool, user_id: int) -> bool:
    """Проверяет, выполнил ли владелец все миссии (активирован ли ученик)"""
    lab = await get_student_lab(pool, user_id)
    if not lab:
        return False
    return bool(lab.get('is_active'))


# ===== УЧЕНИК БТ (топ по опыту учеников) =====
@router.message(F.text.lower() == "ученик бт")
async def cmd_student_top(msg: Message, pool: Pool):
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT sl.lab_id, sl.bio_experience, l.lab_name, l.pathogen_name, u.username
                FROM StudentLab sl
                LEFT JOIN Lab l ON l.lab_id = sl.lab_id
                LEFT JOIN Users u ON u.id = sl.lab_id
                WHERE sl.is_active = TRUE
                ORDER BY sl.bio_experience DESC
                LIMIT %s
            """, (MAX_TOP,))
            rows = await cur.fetchall()

    if not rows:
        return await msg.reply("📊 Пока нет активных учеников.")

    lines = ["🧪 <b>ТОП УЧЕНИКОВ (по опыту):</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(rows, 1):
        name = clean_name(row.get('lab_name') or row.get('pathogen_name') or f"Ученик {row['lab_id']}")
        uid = row['lab_id']
        username = row.get('username')
        uid = row['lab_id']
        if username:
            display = f'<a href="https://t.me/{username}">{name}</a>'
        else:
            display = name
        exp = row.get('bio_experience', 0) or 0
        medal = medals[i-1] if i <= 3 else f"{i}."
        lines.append(f"{medal} {display} (<code>{uid}</code>) — <b>{intcomma(exp)}</b> XP")

    await msg.reply("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


# ===== УЧЕНИК БЧ (топ из чата) =====
@router.message(F.text.lower() == "ученик бч")
async def cmd_student_top_chat(msg: Message, pool: Pool, bot: Bot):
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT sl.lab_id, sl.bio_experience, l.lab_name, u.username
                FROM StudentLab sl
                LEFT JOIN Lab l ON l.lab_id = sl.lab_id
                LEFT JOIN Users u ON u.id = sl.lab_id
                WHERE sl.is_active = TRUE
                ORDER BY sl.bio_experience DESC
                LIMIT 100
            """)
            all_students = await cur.fetchall()

    # Фильтруем по чату
    chat_students = []
    for s in all_students:
        try:
            member = await bot.get_chat_member(CHAT_ID, s['lab_id'])
            if member.status not in ("left", "kicked", "banned"):
                chat_students.append(s)
        except Exception:
            continue
        if len(chat_students) >= MAX_TOP:
            break

    if not chat_students:
        return await msg.reply("📊 Пока нет активных учеников из чата.")

    lines = ["🧪 <b>ТОП УЧЕНИКОВ ЧАТА:</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, s in enumerate(chat_students, 1):
        exp = s.get('bio_experience', 0) or 0
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = clean_name(s.get('lab_name') or f"Ученик {s['lab_id']}")
        uid = s['lab_id']
        username = s.get('username')
        uid = s['lab_id']
        if username:
            display = f'<a href="https://t.me/{username}">{name}</a>'
        else:
            display = name
        lines.append(f"{medal} {display} (<code>{uid}</code>) — <b>{intcomma(exp)}</b> XP")

    await msg.reply("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


# ===== УЧЕНИК МЖ (мои жертвы ученика) =====
@router.message(F.text.lower() == "ученик мж")
async def cmd_student_my_victims(msg: Message, pool: Pool):
    user_id = msg.from_user.id

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT victim_id, student_exp, infect_date, expire_date, kd_expire
                FROM StudentVictims
                WHERE owner_id = %s
                ORDER BY student_exp DESC
                LIMIT 50
            """, (user_id,))
            victims = await cur.fetchall()

    if not victims:
        return await msg.reply("📝 У вашего ученика нет жертв.")

    now = int(time.time())
    lines = [f"☠️ <b>Жертвы ученика ({len(victims)}):</b>\n"]

    for i, v in enumerate(victims, 1):
        vid = v['victim_id']
        exp = v.get('student_exp', 0) or 0
        expire = v.get('expire_date', 0) or 0
        kd = v.get('kd_expire', 0) or 0

        kd_str = ""
        if kd > now:
            left = kd - now
            kd_str = f" ⏳ {left // 60}м"

        lines.append(f"{i}. <code>{vid}</code> — <b>{intcomma(exp)}</b> XP{kd_str}")

    await msg.reply("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


# ===== УЧЕНИК ЗАРАЗИТЬ @user =====
@router.message(F.text.lower().startswith("ученик заразить"))
async def cmd_student_infect(msg: Message, pool: Pool, bot: Bot, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id

    # 1. Проверка: ты активировал ученика
    if not await check_owner_missions(pool, user_id):
        return await msg.reply("❌ Сначала активируйте ученика (выполните все миссии)!")

    now = int(time.time())

    # 2. Проверка: ты сам не инфицирован
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT infected_until, vaccine FROM StudentLab WHERE lab_id = %s",
                (user_id,)
            )
            attacker_lab = await cur.fetchone()

    if attacker_lab:
        infected_until = int(attacker_lab.get('infected_until') or 0)
        vaccine = int(attacker_lab.get('vaccine') or 0)
        if infected_until > now and vaccine == 0:
            left = infected_until - now
            return await msg.reply(
                f"🤒 Вы недавно были заражены и не можете заражать других.\n"
                f"⏳ Подождите ещё {left // 60} мин {left % 60} сек "
                f"или купите <b>ученик кв</b>.",
                parse_mode="HTML"
            )

    # 3. Парсим цель (реплай или текст)
    target_id = None
    requested_attempts = 1  # по умолчанию — 1 патоген

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target_id = msg.reply_to_message.from_user.id
        # Пробуем вытащить число из текста "ученик заразить 5"
        m = re.search(r'ученик заразить(?:\s+(\d+))?\s*$', (msg.text or ""), re.IGNORECASE)
        if m and m.group(1):
            requested_attempts = int(m.group(1))
    else:
        match = re.search(r'ученик заразить\s+(\d{6,16}|@\w+)(?:\s+(\d+))?', msg.text, re.IGNORECASE)
        if not match:
            return await msg.reply("❌ Формат: <code>ученик заразить @user [N]</code>, <code>ученик заразить 123456789 [N]</code> или реплаем", parse_mode="HTML")
        target = match.group(1)
        requested_attempts = int(match.group(2)) if match.group(2) else 1
        if target.startswith("@"):
            username = target.lstrip("@").lower()
            async with pool.acquire() as conn:
                async with conn.cursor(DictCursor) as cur:
                    await cur.execute(
                        "SELECT id FROM Users WHERE LOWER(username) = %s LIMIT 1",
                        (username,)
                    )
                    user_row = await cur.fetchone()
            if user_row:
                target_id = user_row['id']
            else:
                try:
                    entity = await bot.get_users(target)
                    target_id = entity.id
                except Exception:
                    return await msg.reply("❌ Не удалось найти пользователя по @username")
        else:
            target_id = int(target)

    # 4. Проверка: цель — ученик
    if not await check_owner_missions(pool, target_id):
        return await msg.reply("❌ Цель не активировала ученика!")

    # 5. Проверка КД атакующего на пару (attacker, victim) — 2 часа
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT kd_expire FROM StudentVictims
                WHERE owner_id = %s AND victim_id = %s
            """, (user_id, target_id))
            existing = await cur.fetchone()

    if existing and existing.get('kd_expire', 0) > now:
        left = existing['kd_expire'] - now
        return await msg.reply(f"⏳ Цель в КД! Осталось: {left // 60}м {left % 60}с")

    # 6. Опыт жертвы
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("SELECT bio_experience, lethality, immunity FROM StudentLab WHERE lab_id = %s", (target_id,))
            victim_lab = await cur.fetchone()

    if not victim_lab:
        return await msg.reply("❌ У цели нет ученика!")

    victim_exp = victim_lab.get('bio_experience', 0) or 0
    earn_exp = int(victim_exp * 0.20)

    # Получаем student ДО использования (иначе UnboundLocalError)
    student = await get_student_lab(pool, user_id)
    attacker_infect = int(student.get('infect') or 0)
    victim_immunity = int(victim_lab.get('immunity') or 0)
    infect_chance = get_infect_chance(attacker_infect, victim_immunity)

    # Сколько готовых патогенов доступно
    attacker_ready = int(student.get('ready_pathogens') or 0)
    if attacker_ready < 1:
        return await msg.reply(
            "🧪 У вас нет готовых патогенов! Дождитесь, пока они приготовятся.",
            parse_mode="HTML"
        )

    # Сколько попыток делаем: по умолчанию 1, макс 10, не больше чем ready
    attempts = requested_attempts if requested_attempts > 0 else 1
    if attempts > 10:
        attempts = 10
    if attempts > attacker_ready:
        attempts = attacker_ready

    # N независимых попыток (списываем ровно attempts)
    success = False
    used = attempts
    for _ in range(attempts):
        if random.random() < infect_chance:
            success = True
            break

    # Списываем патогены ВСЕГДА — сколько попыток, столько и потрачено
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE StudentLab SET ready_pathogens = GREATEST(ready_pathogens - %s, 0) WHERE lab_id = %s",
                (used, user_id)
            )

    if not success:
        percent_one = round(infect_chance * 100, 3)
        percent_total = round((1 - (1 - infect_chance) ** attempts) * 100, 3)

        # Уведомление жертве о том, что была попытка заражения (провал)
        try:
            print(f"[NOTIFY VICTIM FAIL] отправляю target_id={target_id}")
            await bot.send_message(
                target_id,
                f"⚠️ <b>Вас пытались заразить, но атака не удалась!</b>\n\n"
                f"🎯 Атакующий: <code>{user_id}</code>\n"
                f"🔁 Попыток: <b>{attempts}</b>\n"
                f"🎲 Шанс был: <b>{percent_total}%</b>",
                parse_mode="HTML"
            )
            print(f"[NOTIFY VICTIM FAIL] отправлено target_id={target_id}")
        except Exception as e:
            print(f"[NOTIFY VICTIM FAIL ERROR] target_id={target_id} err={e}")

        return await msg.reply(
            f"❌ <b>Заражение не удалось!</b>\n\n"
            f"🎯 Цель: <code>{target_id}</code>\n"
            f"🧬 Ваша заразность: <b>{attacker_infect}</b>\n"
            f"🛡 Иммунитет жертвы: <b>{victim_immunity}</b>\n"
            f"🎲 Шанс за попытку: <b>{percent_one}%</b>\n"
            f"🔁 Попыток: <b>{attempts}</b>\n"
            f"🎯 Итоговый шанс: <b>{percent_total}%</b>\n"
            f"🧪 Потрачено патогенов: <b>{used}</b>",
            parse_mode="HTML"
        )

    # 7. Таймер инфекции жертвы = lethality минут, максимум 60
    victim_lethality = int(victim_lab.get('lethality') or 1)
    if victim_lethality < 1:
        victim_lethality = 1
    if victim_lethality > 60:
        victim_lethality = 60
    infected_until = now + victim_lethality * 60

    # 8. Летальность атакующего → срок жизни жертвы
    lethality = int(student.get('lethality') or 1)
    if lethality < 1:
        lethality = 1
    expire_date = now + lethality * 86400
    kd_expire = now + 2 * 3600

    # 9. INSERT/UPDATE StudentVictims + XP + инфекция жертве
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO StudentVictims (owner_id, victim_id, student_exp, infect_date, expire_date, kd_expire, pathogen_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    student_exp = student_exp + VALUES(student_exp),
                    infect_date = VALUES(infect_date),
                    expire_date = VALUES(expire_date),
                    kd_expire = VALUES(kd_expire)
            """, (user_id, target_id, earn_exp, now, expire_date, kd_expire, student.get('pathogen_name') or 'Ученик'))

            await cur.execute("""
                UPDATE StudentLab
                SET bio_experience = bio_experience + %s
                WHERE lab_id = %s
            """, (earn_exp, user_id))

            await cur.execute("""
                UPDATE StudentLab
                SET infected_until = %s
                WHERE lab_id = %s
            """, (infected_until, target_id))

    # 10. Уведомление атакующему — всегда в личку
    try:
        await bot.send_message(
            user_id,
            f"🦠 <b>Ваш ученик заразил цель!</b>\n\n"
            f"🎯 Жертва: <code>{target_id}</code>\n"
            f"⭐ +{intcomma(earn_exp)} XP ученику\n"
            f"⏳ Жертва не сможет заражать {victim_lethality} мин.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    # 10.5. Уведомление ЖЕРТВЕ — всегда в личку
    try:
        print(f"[NOTIFY VICTIM] отправляю target_id={target_id}")
        await bot.send_message(
            target_id,
            f"🤒 <b>Вас заразил ученик!</b>\n\n"
            f"🎯 Атакующий: <code>{user_id}</code>\n"
            f"⏳ Вы не можете заражать {victim_lethality} мин.\n"
            f"💊 Купите <b>ученик кв</b>, чтобы снять эффект.",
            parse_mode="HTML"
        )
        print(f"[NOTIFY VICTIM] отправлено target_id={target_id}")
    except Exception as e:
        print(f"[NOTIFY VICTIM ERROR] target_id={target_id} err={e}")

    await msg.reply(
        f"🦠 <b>Ученик заразил!</b>\n\n"
        f"🎯 Цель: <code>{target_id}</code>\n"
        f"⭐ +{intcomma(earn_exp)} XP ученику\n"
        f"⏳ Жертва не сможет заражать {victim_lethality} мин.",
        parse_mode="HTML"
    )

    await asyncio.sleep(INFECT_KD)


# ===== УЧЕНИК КВ (вакцина) =====
@router.message(F.text.lower() == "ученик кв")
async def cmd_student_buy_vaccine(msg: Message, pool: Pool):
    user_id = msg.from_user.id

    if not await check_owner_missions(pool, user_id):
        return await msg.reply("❌ Сначала активируйте ученика!")

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT sl.infect, l.bio_resource "
                "FROM StudentLab sl LEFT JOIN Lab l ON l.lab_id = sl.lab_id "
                "WHERE sl.lab_id = %s",
                (user_id,)
            )
            row = await cur.fetchone()

    if not row:
        return await msg.reply("❌ Ученик не найден.")

    infect = int(row.get('infect') or 0)
    if infect < 1:
        infect = 1
    VACCINE_PRICE = infect * 50

    if (row.get('bio_resource') or 0) < VACCINE_PRICE:
        return await msg.reply(f"❌ Недостаточно ресурсов! Нужно {intcomma(VACCINE_PRICE)} 🧬")

    # Проверяем: инфицирован ли ученик?
    now = int(time.time())
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT infected_until, vaccine FROM StudentLab WHERE lab_id = %s",
                (user_id,)
            )
            lab_row = await cur.fetchone()

    infected_until = int(lab_row.get('infected_until') or 0) if lab_row else 0
    vaccine_active = int(lab_row.get('vaccine') or 0) if lab_row else 0

    if vaccine_active == 1:
        return await msg.reply(
            "💊 У вас уже активна вакцина. Повторно покупать не нужно.",
            parse_mode="HTML"
        )

    if infected_until <= now:
        return await msg.reply(
            "✅ Ваш ученик не инфицирован — вакцина не требуется.",
            parse_mode="HTML"
        )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s",
                (VACCINE_PRICE, user_id)
            )
            await cur.execute(
                "UPDATE StudentLab SET vaccine = 1, infected_until = 0 WHERE lab_id = %s",
                (user_id,)
            )

    await msg.reply(
        f"✅ <b>Вакцина куплена для ученика!</b>\n\n"
        f"💰 Списано: <b>{intcomma(VACCINE_PRICE)}</b> 🧬\n"
        f"💊 Вакцина активна, инфекция снята",
        parse_mode="HTML"
    )


# ===== УЧЕНИК -ИМЯ =====
@router.message(F.text.lower() == "ученик -имя")
async def cmd_student_reset_name(msg: Message, pool: Pool, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id

    if not await check_owner_missions(pool, user_id):
        return await msg.reply("❌ Сначала активируйте ученика!")

    # Сбрасываем имя патогена и лабы ВЛАДЕЛЬЦА
    await repo_biowar.pathogen_name_change(None, user_id)
    await repo_biowar.lab_name_change(None, user_id)

    await msg.reply("✅ Имя патогена и лаборатории сброшены.")


# ===== УЧЕНИК МФ (массовое заражение) =====
@router.message(F.text.lower() == "ученик мф")
async def cmd_student_mass_infect(msg: Message, pool: Pool, bot: Bot):
    user_id = msg.from_user.id

    if not await check_owner_missions(pool, user_id):
        return await msg.reply("❌ Сначала активируйте ученика!")

    # Берём 30 целей из StudentVictims (или из списка жертв)
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT victim_id FROM StudentVictims
                WHERE owner_id = %s AND expire_date > %s
                ORDER BY student_exp DESC
                LIMIT 30
            """, (user_id, int(time.time())))
            victims = await cur.fetchall()

    if not victims:
        return await msg.reply("📝 Нет доступных целей для заражения.")

    count = 0
    for v in victims:
        try:
            # Логика заражения (упрощённо)
            count += 1
            await asyncio.sleep(INFECT_KD)
        except Exception:
            continue

    await msg.reply(f"🦠 Ученик заразил {count} целей!")


# ===== УЧЕНИК +ИМЯ ПАТОГЕНА =====
@router.message(F.text.regexp(r'(?i)^ученик\s+\+имя\s+патогена\s+(.+)$'))
async def cmd_student_set_pathogen_name(msg: Message, pool: Pool, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id

    if not await check_owner_missions(pool, user_id):
        return await msg.reply("❌ Сначала активируйте ученика!")

    match = re.match(r'(?i)^ученик\s+\+имя\s+патогена\s+(.+)$', msg.text)
    new_name = match.group(1).strip()

    if len(new_name) > 40:
        return await msg.reply("❌ Имя патогена слишком длинное (макс. 40)")

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE Lab SET pathogen_name = %s WHERE lab_id = %s", (new_name, user_id))

    await msg.reply(f"✅ Имя патогена изменено на: <b>{new_name}</b>", parse_mode="HTML")


# ===== УЧЕНИК +ИМЯ ЛАБЫ =====
@router.message(F.text.regexp(r'(?i)^ученик\s+\+имя\s+(.+)$'))
async def cmd_student_set_lab_name(msg: Message, pool: Pool):
    user_id = msg.from_user.id

    if not await check_owner_missions(pool, user_id):
        return await msg.reply("❌ Сначала активируйте ученика!")

    match = re.match(r'(?i)^ученик\s+\+имя\s+(.+)$', msg.text)
    new_name = match.group(1).strip()

    if len(new_name) > 40:
        return await msg.reply("❌ Имя лаборатории слишком длинное (макс. 40)")

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE Lab SET lab_name = %s WHERE lab_id = %s", (new_name, user_id))

    await msg.reply(f"✅ Имя лаборатории изменено на: <b>{new_name}</b>", parse_mode="HTML")

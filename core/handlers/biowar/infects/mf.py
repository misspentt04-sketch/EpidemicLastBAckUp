import asyncio
import random
import logging
from html import escape
from datetime import datetime, timedelta
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramRetryAfter
import time

PAGE_SIZE = 20

def get_mf_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    nav_row = []

    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"mf_page:{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"mf_page:{page+1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text=f"☣️ Заразить всех (Стр. {page})", callback_data=f"mf_start:{page}")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔥 Заразить ВСЕХ из списка", callback_data="mf_start_all")
    ])
    # КНОПКА ОЧИСТКИ ОТКЛЮЧЕНА (баг с удалением всех жертв)
    # buttons.append([
    #     InlineKeyboardButton(text="🧹 Очистить слетевших", callback_data="mf_cleanup")
    # ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_kb():
    """Клавиатура отмены во время МФ"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Остановить заражение", callback_data="mf_cancel")]
    ])


def format_mf_text(fallen_list: list, page: int, total_pages: int) -> str:
    start_idx = (page - 1) * PAGE_SIZE
    page_items = fallen_list[start_idx : start_idx + PAGE_SIZE]

    lines = [f"☣️ <b>Список слетевших целей (Страница {page}/{total_pages}):</b>\n"]
    for idx, item in enumerate(page_items, start=start_idx + 1):
        if isinstance(item, dict):
            name = item.get('full_name') or item.get('username') or f"ID: {item.get('victim_id')}"
            lines.append(f"{idx}. {escape(str(name))}")
        else:
            lines.append(f"{idx}. ID: {escape(str(item))}")

    return "\n".join(lines)


async def cmd_mass_fallen(msg: Message, repo_biowar):
    user_id = msg.from_user.id
    fallen_list = await repo_biowar.get_fallen_targets(user_id)

    if not fallen_list:
        return await msg.answer("❌ У вас нет доступных слетевших целей!")

    total_pages = max(1, (len(fallen_list) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = 1

    text = format_mf_text(fallen_list, page, total_pages)
    kb = get_mf_keyboard(page, total_pages)

    await msg.answer(text, reply_markup=kb, parse_mode="HTML")


async def process_mf_page(call: CallbackQuery, repo_biowar):
    page = int(call.data.split(":")[1])
    user_id = call.from_user.id

    fallen_list = await repo_biowar.get_fallen_targets(user_id)
    if not fallen_list:
        return await call.answer("❌ Список целей пуст!", show_alert=True)

    total_pages = max(1, (len(fallen_list) + PAGE_SIZE - 1) // PAGE_SIZE)
    text = format_mf_text(fallen_list, page, total_pages)
    kb = get_mf_keyboard(page, total_pages)

    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.answer("❌ Сообщение устарело, откройте мф заново", show_alert=True)


async def process_mf_start(call: CallbackQuery, repo_biowar, redis=None):
    page = int(call.data.split(":")[1])
    user_id = call.from_user.id

    fallen_list = await repo_biowar.get_fallen_targets(user_id)
    start_idx = (page - 1) * PAGE_SIZE
    targets_on_page = fallen_list[start_idx : start_idx + PAGE_SIZE]

    if not targets_on_page:
        return await call.answer("❌ На этой странице нет доступных целей!", show_alert=True)

    await call.answer("🚀 Запуск массовой атаки...")

    status_msg = await call.message.answer(
        f"☣️ <b>Инициализация массового заражения...</b>\n"
        f"🎯 Всего целей: <b>{len(targets_on_page)}</b>",
        parse_mode="HTML"
    )

    success_cnt = 0
    fail_cnt = 0
    total_exp = 0
    total_spent_pathogens = 0
    idx_processed = 0
    success_list = []  # список успешных (имя, exp)
    fail_list = []     # список промахов (имя)

    chance_table = {
        -1: 50.0, -2: 35.0, -3: 25.0, -4: 18.0, -5: 12.0,
        -6: 8.0,  -7: 5.0,  -8: 3.0,  -9: 2.0,  -10: 1.0,
        -11: 0.8, -12: 0.6, -13: 0.4, -14: 0.3, -15: 0.3,
        -16: 0.2, -17: 0.2, -18: 0.2, -19: 0.2, -20: 0.2,
        -21: 0.1, -22: 0.1, -23: 0.1, -24: 0.1, -25: 0.1,
        -26: 0.1, -27: 0.1, -28: 0.1, -29: 0.1
    }

    try:
        from core.handlers.biowar.infects.infect import tricks_biowar
        claim_percent = tricks_biowar.get('max', {}).get('elements', {}).get('infect_claim_percent', 0.05)
    except Exception:
        claim_percent = 0.05

    # ===== ЗАГРУЖАЕМ ВСЕХ ЖЕРТВ ПАЧКОЙ =====
    victim_ids = []
    for t in targets_on_page:
        if isinstance(t, dict):
            vid = t.get('victim_id') or t.get('id')
        else:
            vid = t
        if vid:
            victim_ids.append(int(vid))

    victims_map = {}
    if victim_ids:
        try:
            placeholders = ','.join(['%s'] * len(victim_ids))
            await repo_biowar.cur.execute(
                f"SELECT * FROM Lab WHERE lab_id IN ({placeholders})",
                victim_ids
            )
            rows = await repo_biowar.cur.fetchall()
            for row in rows:
                if isinstance(row, dict):
                    victims_map[row['lab_id']] = row
        except Exception as e:
            logging.error(f"[MF BULK LOAD ERROR]: {e}")

    # ===== ОДИН РАЗ ЧИТАЕМ АТАКУЮЩЕГО =====
    infecter = await repo_biowar.get_info_user_lab(user_id)
    if isinstance(infecter, (list, tuple)):
        infecter = infecter[0] if infecter else {}

    if not infecter or not isinstance(infecter, dict):
        logging.error(f"[MF ERROR] Не удалось получить данные лабы user_id={user_id}")
        return

    # Локальный счётчик патогенов (чтобы не читать БД каждый раз)
    current_pathogens = infecter.get('ready_pathogens', 0) or 0
    logging.info(f"[MF START ALL] user={user_id}, патогенов={current_pathogens}, целей={len(fallen_list)}")

    last_edit_time = 0  # время последнего edit

    # Установить флаг активного МФ
    if redis:
        try:
            await redis.set(f"mf_active:{user_id}", "1", ex=3600)
        except Exception:
            pass

    cancel_kb = get_cancel_kb()
    status_msg = await status_msg.edit_reply_markup(reply_markup=cancel_kb)

    for idx, target in enumerate(targets_on_page, 1):
        idx_processed = idx

        # Проверяем отмену
        if redis:
            try:
                flag = await redis.get(f"mf_active:{user_id}")
                if flag and (flag == b"0" or flag == "0"):
                    logging.info(f"[MF] Отменено пользователем на {idx}")
                    await status_msg.edit_text("❌ <b>Массовое заражение остановлено!</b>", parse_mode="HTML")
                    break
            except Exception:
                pass

        if isinstance(target, dict):
            victim_id = target.get('victim_id') or target.get('id')
            display_name = target.get('full_name') or target.get('username') or f"ID: {victim_id}"
            display_name = escape(str(display_name))
        else:
            victim_id = target
            display_name = f"ID: {escape(str(victim_id))}"

        ready_pathogens = infecter.get('ready_pathogens', 0) or 0

        # Остановка при отсутствии патогенов
        if ready_pathogens < 1:
            await status_msg.reply("⚠️ <b>Массовое заражение остановлено:</b> закончились патогены!")
            break

        victimer = victims_map.get(int(victim_id), {})
        if not victimer:
            logging.warning(f"[MF SKIP] Пропуск цели {victim_id}: не найдены данные лабы")
            fail_cnt += 1
            continue

        # 2. ПРИНУДИТЕЛЬНОЕ СПИСАНИЕ В БД И ОБНОВЛЕНИЕ ЛОКАЛЬНОГО СЧЕТЧИКА
        try:
            await repo_biowar.subtract_pathogens(user_id, 1)
            current_pathogens -= 1
        except Exception as e:
            logging.error(f"[MF SUBTRACT ERROR]: {e}")
            # Если subtract упал — вероятно, патогенов нет
            current_pathogens = 0
            break

        total_spent_pathogens += 1
        new_ready_pathogens = max(0, current_pathogens)

        inf_infect = infecter.get('infect', 1) or 1
        vic_immunity = victimer.get('immunity', 0) or 0
        difference = inf_infect - vic_immunity

        if difference >= 0:
            base_chance = 100.0
        else:
            base_chance = chance_table.get(difference, 0.1)

        accum_bonus = 0.0
        redis_key = f"infect_accum_bonus:{user_id}:{victim_id}"
        if redis:
            try:
                raw_accum = await redis.get(redis_key)
                if raw_accum:
                    accum_bonus = float(raw_accum)
            except Exception as e:
                logging.error(f"[MF REDIS ERROR]: {e}")

        step_add = 0.05 if difference <= -30 else base_chance / 3.0
        current_chance = round(min(100.0, base_chance + accum_bonus), 2)

        is_success = False

        if random.random() * 100 <= current_chance:
            is_success = True
            if redis:
                try:
                    await redis.delete(redis_key)
                except Exception:
                    pass
        else:
            if redis:
                try:
                    accum_bonus += step_add
                    await redis.set(redis_key, accum_bonus, ex=60)
                except Exception:
                    pass

        if is_success:
            success_cnt += 1

            vic_base_exp = victimer.get('bio_experience', 0) or 0
            earn_exp = int(round(vic_base_exp * claim_percent, 0))

            if vic_immunity > inf_infect:
                earn_exp = int(round(earn_exp / (1 + (vic_immunity - inf_infect) / 100), 0))

            earn_exp = max(1, earn_exp)
            total_exp += earn_exp
            success_list.append((display_name, earn_exp))

            lose_exp = victimer.get('bio_experience', 0) - earn_exp
            vic_exp = max(0, lose_exp)

            lethality = infecter.get('lethality', 1) or 1
            now = datetime.utcnow()
            vic_expire = int((now + timedelta(days=lethality)).timestamp())
            vic_expire_kd = int((now + timedelta(hours=1)).timestamp())
            infect_date = int(now.timestamp())
            pathogen_name = infecter.get('pathogen_name') or 'Патоген'

            try:
                # В infect_setup передаём уже актуальное уменьшенное число new_ready_pathogens
                await repo_biowar.infect_setup(
                    user_id,
                    int(victim_id),
                    earn_exp,
                    vic_exp,
                    vic_expire_kd,
                    new_ready_pathogens,
                    0,
                    vic_expire,
                    infect_date,
                    pathogen_name,
                    0,
                    infecter.get('science_time', 0),
                    False,
                    0
                )
            except Exception as e:
                logging.error(f"[MF INFECT SETUP ERROR]: {e}")

            status_text = f"🟢 <b>ПРОБИТО!</b> (+{earn_exp:,} XP)"
        else:
            fail_cnt += 1
            fail_list.append(display_name)
            status_text = f"🔴 <b>ПРОМАХ!</b>"

        percent = int((idx / len(targets_on_page)) * 100)
        filled = int(percent // 10)
        bar = "▓" * filled + "░" * (10 - filled)

        # Обновляем статус не чаще раза в 2 секунды + обрабатываем flood
        if time.time() - last_edit_time >= 2.0 or idx == len(targets_on_page):
            try:
                await status_msg.edit_text(
                    f"☣️ <b>Массовое заражение в процессе ({idx}/{len(targets_on_page)})...</b>\n\n"
                    f"🎯 Цель: <b>{display_name}</b>\n"
                    f"🎲 Шанс пробития: <b>{current_chance}%</b>\n"
                    f"🧪 Оставшиеся патогены: <b>{new_ready_pathogens}</b>\n"
                    f"Результат: {status_text}\n\n"
                    f"📊 Прогресс: <code>[{bar}] {percent}%</code>\n"
                    f"🟢 Успешно: <b>{success_cnt}</b> | 🔴 Промахи: <b>{fail_cnt}</b>",
                    parse_mode="HTML"
                )
                last_edit_time = time.time()
            except TelegramRetryAfter as e:
                logging.warning(f"[MF FLOOD] Ждём {e.retry_after} сек")
                await asyncio.sleep(e.retry_after)
                last_edit_time = time.time()
            except Exception as e:
                logging.error(f"[MF EDIT ERROR]: {e}")

        # Пауза между жертвами
        await asyncio.sleep(0.3)

    report_lines = [
        f"☣️ <b>Итоги массового заражения (Стр. {page}):</b>\n",
        f"🎯 Обработано целей: <b>{idx_processed} / {len(targets_on_page)}</b>",
        f"🟢 Пробито целей: <b>{success_cnt}</b>",
        f"🔴 Не пробито: <b>{fail_cnt}</b>",
        f"🧪 Потрачено патогенов: <b>{total_spent_pathogens}</b>\n",
        f"📈 <b>Получено опыта:</b>",
        f"🧬 <b>+{total_exp:,} XP</b>",
    ]

    # 🟢 Успешные
    if success_list:
        report_lines.append(f"\n🟢 <b>Пробитые цели:</b>")
        for name, exp in success_list:
            report_lines.append(f"  ✅ {name} — <b>+{exp:,} XP</b>")

    # 🔴 Промахи
    if fail_list:
        report_lines.append(f"\n🔴 <b>Не пробитые:</b>")
        for name in fail_list:
            report_lines.append(f"  ❌ {name}")

    report = "\n".join(report_lines)
    try:
        await status_msg.edit_text(report, parse_mode="HTML")
    except Exception as e:
        logging.error(f"[MF] Ошибка при редактировании финального сообщения: {e}")
        await call.message.answer(report, parse_mode="HTML")


# ===== ОЧИСТКА СЛЕТЕВШИХ =====
async def cleanup_expired_victims(repo_biowar, owner_id: int) -> int:
    """Удаляет ТОЛЬКО мёртвых Victims (victim_expire < now). Историю НЕ трогает."""
    now_ts = int(time.time())

    try:
        await repo_biowar.cur.execute(
            "SELECT COUNT(*) AS cnt FROM Victims WHERE victims_owner_id = %s AND victim_expire < %s",
            (owner_id, now_ts)
        )
        row = await repo_biowar.cur.fetchone()
        count = 0
        if row:
            if isinstance(row, dict):
                count = row.get('cnt', 0) or 0
            elif isinstance(row, (list, tuple)):
                count = row[0] or 0

        logging.info(f"[MF CLEANUP] user={owner_id}, найдено мёртвых: {count}")

        if count > 0:
            await repo_biowar.cur.execute(
                "DELETE FROM Victims WHERE victims_owner_id = %s AND victim_expire < %s",
                (owner_id, now_ts)
            )
            logging.info(f"[MF CLEANUP] удалено: {count}")

        return count
    except Exception as e:
        logging.error(f"[MF CLEANUP ERROR]: {e}")
        return 0


async def process_mf_cleanup(call: CallbackQuery, repo_biowar):
    """Callback: очистить слетевших"""
    user_id = call.from_user.id
    count = await cleanup_expired_victims(repo_biowar, user_id)
    await call.answer(f"🧹 Удалено: {count} слетевших жертв", show_alert=True)

    # Обновляем меню
    fallen_list = await repo_biowar.get_fallen_targets(user_id)
    if not fallen_list:
        try:
            await call.message.edit_text("❌ Список слетевших целей пуст!", parse_mode="HTML")
        except Exception:
            pass
        return

    total_pages = max(1, (len(fallen_list) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = 1
    text = format_mf_text(fallen_list, page, total_pages)
    kb = get_mf_keyboard(page, total_pages)

    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass


# ===== ЗАРАЗИТЬ ВСЕХ ИЗ СПИСКА =====
async def process_mf_start_all(call: CallbackQuery, repo_biowar, redis=None):
    """Заражает ВСЕХ слетевших из списка (не только текущую страницу)"""
    user_id = call.from_user.id

    fallen_list = await repo_biowar.get_fallen_targets(user_id)
    if not fallen_list:
        return await call.answer("❌ Список слетевших пуст!", show_alert=True)

    total = len(fallen_list)
    await call.answer(f"🚀 Запуск массовой атаки на {total} целей...")

    status_msg = await call.message.answer(
        f"☣️ <b>Инициализация массового заражения...</b>\n"
        f"🎯 Всего целей: <b>{total}</b>",
        parse_mode="HTML"
    )

    success_cnt = 0
    fail_cnt = 0
    total_exp = 0
    total_spent_pathogens = 0
    idx_processed = 0
    success_list = []
    fail_list = []

    chance_table = {
        -1: 50.0, -2: 35.0, -3: 25.0, -4: 18.0, -5: 12.0,
        -6: 8.0,  -7: 5.0,  -8: 3.0,  -9: 2.0,  -10: 1.0,
        -11: 0.8, -12: 0.6, -13: 0.4, -14: 0.3, -15: 0.3,
        -16: 0.2, -17: 0.2, -18: 0.2, -19: 0.2, -20: 0.2,
        -21: 0.1, -22: 0.1, -23: 0.1, -24: 0.1, -25: 0.1,
        -26: 0.1, -27: 0.1, -28: 0.1, -29: 0.1
    }

    try:
        from core.handlers.biowar.infects.infect import tricks_biowar
        claim_percent = tricks_biowar.get('max', {}).get('elements', {}).get('infect_claim_percent', 0.05)
    except Exception:
        claim_percent = 0.05

    infecter = await repo_biowar.get_info_user_lab(user_id)
    if isinstance(infecter, (list, tuple)):
        infecter = infecter[0] if infecter else {}

    if not infecter or not isinstance(infecter, dict):
        logging.error(f"[MF ERROR] Не удалось получить данные лабы user_id={user_id}")
        return

    # ← ИНИЦИАЛИЗАЦИЯ СЧЁТЧИКА ПАТОГЕНОВ
    current_pathogens = int(infecter.get('ready_pathogens', 0) or 0)

    # Ограничиваем список патогенами (не больше, чем есть)
    if len(fallen_list) > current_pathogens:
        fallen_list = fallen_list[:current_pathogens]
        total = len(fallen_list)

    last_edit_time = 0

    # Установить флаг активного МФ
    if redis:
        try:
            await redis.set(f"mf_active:{user_id}", "1", ex=3600)
        except Exception:
            pass

    cancel_kb = get_cancel_kb()
    try:
        await status_msg.edit_reply_markup(reply_markup=cancel_kb)
    except Exception:
        pass

    for idx, target in enumerate(fallen_list, 1):
        idx_processed = idx

        # Проверяем отмену
        if redis:
            try:
                flag = await redis.get(f"mf_active:{user_id}")
                if flag and (flag == b"0" or flag == "0"):
                    logging.info(f"[MF ALL] Отменено пользователем на {idx}")
                    await status_msg.edit_text("❌ <b>Массовое заражение остановлено!</b>", parse_mode="HTML")
                    break
            except Exception:
                pass

        if isinstance(target, dict):
            victim_id = target.get('victim_id') or target.get('id')
            display_name = target.get('full_name') or target.get('username') or f"ID: {victim_id}"
            display_name = escape(str(display_name))
        else:
            victim_id = target
            display_name = f"ID: {escape(str(victim_id))}"

        if current_pathogens < 1:
            await status_msg.reply("⚠️ <b>Массовое заражение остановлено:</b> закончились патогены!")
            break

        victimer = await repo_biowar.get_info_user_lab(victim_id) if victim_id else None
        if isinstance(victimer, (list, tuple)):
            victimer = victimer[0] if victimer else {}

        if not victimer or not isinstance(victimer, dict):
            fail_cnt += 1
            fail_list.append(display_name)
            continue

        try:
            await repo_biowar.subtract_pathogens(user_id, 1)
            current_pathogens -= 1
        except Exception as e:
            logging.error(f"[MF SUBTRACT ERROR]: {e}")
            # Если subtract упал — вероятно, патогенов нет
            current_pathogens = 0
            break

        total_spent_pathogens += 1
        new_ready_pathogens = max(0, current_pathogens)

        inf_infect = infecter.get('infect', 1) or 1
        vic_immunity = victimer.get('immunity', 0) or 0
        difference = inf_infect - vic_immunity

        if difference >= 0:
            base_chance = 100.0
        else:
            base_chance = chance_table.get(difference, 0.1)

        accum_bonus = 0.0
        redis_key = f"infect_accum_bonus:{user_id}:{victim_id}"
        if redis:
            try:
                raw_accum = await redis.get(redis_key)
                if raw_accum:
                    accum_bonus = float(raw_accum)
            except Exception:
                pass

        step_add = 0.05 if difference <= -30 else base_chance / 3.0
        current_chance = round(min(100.0, base_chance + accum_bonus), 2)

        is_success = False
        if random.random() * 100 <= current_chance:
            is_success = True
            if redis:
                try:
                    await redis.delete(redis_key)
                except Exception:
                    pass
        else:
            if redis:
                try:
                    accum_bonus += step_add
                    await redis.set(redis_key, accum_bonus, ex=60)
                except Exception:
                    pass

        if is_success:
            success_cnt += 1
            vic_base_exp = victimer.get('bio_experience', 0) or 0
            earn_exp = int(round(vic_base_exp * claim_percent, 0))
            if vic_immunity > inf_infect:
                earn_exp = int(round(earn_exp / (1 + (vic_immunity - inf_infect) / 100), 0))
            earn_exp = max(1, earn_exp)
            total_exp += earn_exp
            success_list.append((display_name, earn_exp))

            lose_exp = victimer.get('bio_experience', 0) - earn_exp
            vic_exp = max(0, lose_exp)

            lethality = infecter.get('lethality', 1) or 1
            now = datetime.utcnow()
            vic_expire = int((now + timedelta(days=lethality)).timestamp())
            vic_expire_kd = int((now + timedelta(hours=1)).timestamp())
            infect_date = int(now.timestamp())
            pathogen_name = infecter.get('pathogen_name') or 'Патоген'

            try:
                await repo_biowar.infect_setup(
                    user_id, int(victim_id), earn_exp, vic_exp, vic_expire_kd,
                    new_ready_pathogens, 0, vic_expire, infect_date,
                    pathogen_name, 0, infecter.get('science_time', 0), False, 0
                )
            except Exception as e:
                logging.error(f"[MF INFECT SETUP ERROR]: {e}")

            status_text = f"🟢 <b>ПРОБИТО!</b> (+{earn_exp:,} XP)"
        else:
            fail_cnt += 1
            fail_list.append(display_name)
            status_text = f"🔴 <b>ПРОМАХ!</b>"

        percent = int((idx / total) * 100)
        filled = int(percent // 10)
        bar = "▓" * filled + "░" * (10 - filled)

        if time.time() - last_edit_time >= 2.0 or idx == total:
            try:
                await status_msg.edit_text(
                    f"☣️ <b>Массовое заражение ({idx}/{total})...</b>\n\n"
                    f"🎯 Цель: <b>{display_name}</b>\n"
                    f"🎲 Шанс: <b>{current_chance}%</b>\n"
                    f"🧪 Патогены: <b>{new_ready_pathogens}</b>\n"
                    f"Результат: {status_text}\n\n"
                    f"📊 <code>[{bar}] {percent}%</code>\n"
                    f"🟢 {success_cnt} | 🔴 {fail_cnt}",
                    parse_mode="HTML"
                )
                last_edit_time = time.time()
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                last_edit_time = time.time()
            except Exception as e:
                logging.error(f"[MF EDIT ERROR]: {e}")

        await asyncio.sleep(0.3)

    report_lines = [
        f"☣️ <b>Итоги массового заражения (ВСЕ {total}):</b>\n",
        f"🎯 Обработано: <b>{idx_processed} / {total}</b>",
        f"🟢 Пробито: <b>{success_cnt}</b>",
        f"🔴 Не пробито: <b>{fail_cnt}</b>",
        f"🧪 Потрачено патогенов: <b>{total_spent_pathogens}</b>\n",
        f"📈 <b>Получено опыта:</b>",
        f"🧬 <b>+{total_exp:,} XP</b>",
    ]

    if success_list:
        report_lines.append(f"\n🟢 <b>Пробитые цели:</b>")
        for name, exp in success_list[:15]:
            report_lines.append(f"  ✅ {name} — <b>+{exp:,} XP</b>")
        if len(success_list) > 15:
            report_lines.append(f"  <i>...и ещё {len(success_list) - 15}</i>")

    if fail_list:
        report_lines.append(f"\n🔴 <b>Не пробитые:</b>")
        for name in fail_list[:15]:
            report_lines.append(f"  ❌ {name}")
        if len(fail_list) > 15:
            report_lines.append(f"  <i>...и ещё {len(fail_list) - 15}</i>")

    report = "\n".join(report_lines)

    # Сбрасываем флаг МФ
    if redis:
        try:
            await redis.delete(f"mf_active:{user_id}")
        except Exception:
            pass

    try:
        await status_msg.edit_text(report, parse_mode="HTML")
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        try:
            await status_msg.edit_text(report, parse_mode="HTML")
        except Exception:
            pass
    except Exception as e:
        logging.error(f"[MF] Ошибка финального сообщения: {e}")
        try:
            await call.message.answer(report, parse_mode="HTML")
        except Exception:
            pass


# ===== ОТМЕНА МФ =====
async def process_mf_cancel(call: CallbackQuery, redis=None):
    """Callback: отменить активный МФ"""
    user_id = call.from_user.id
    if redis:
        try:
            await redis.set(f"mf_active:{user_id}", "0", ex=300)
        except Exception:
            pass
    await call.answer("❌ Остановка заражения...", show_alert=True)


async def cmd_mf_stop(msg: Message, redis=None):
    """Команда 'мф стоп' или 'мф отмена' — остановить активный МФ"""
    user_id = msg.from_user.id
    if redis:
        try:
            flag = await redis.get(f"mf_active:{user_id}")
            if flag and (flag == b"1" or flag == "1"):
                await redis.set(f"mf_active:{user_id}", "0", ex=300)
                await msg.answer("❌ <b>Массовое заражение будет остановлено после текущей цели.</b>", parse_mode="HTML")
            else:
                await msg.answer("ℹ️ У вас нет активного МФ.")
        except Exception as e:
            logging.error(f"[MF STOP ERROR]: {e}")
            await msg.answer("❌ Ошибка при остановке МФ.")
    else:
        await msg.answer("❌ Redis недоступен.")

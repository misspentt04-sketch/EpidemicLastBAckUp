import asyncio
import random
import logging
from datetime import datetime, timedelta
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

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

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_mf_text(fallen_list: list, page: int, total_pages: int) -> str:
    start_idx = (page - 1) * PAGE_SIZE
    page_items = fallen_list[start_idx : start_idx + PAGE_SIZE]

    lines = [f"☣️ <b>Список слетевших целей (Страница {page}/{total_pages}):</b>\n"]
    for idx, item in enumerate(page_items, start=start_idx + 1):
        if isinstance(item, dict):
            name = item.get('full_name') or item.get('username') or f"ID: {item.get('victim_id')}"
            lines.append(f"{idx}. {name}")
        else:
            lines.append(f"{idx}. ID: {item}")

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

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


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

    for idx, target in enumerate(targets_on_page, 1):
        idx_processed = idx

        if isinstance(target, dict):
            victim_id = target.get('victim_id') or target.get('id')
            display_name = target.get('full_name') or target.get('username') or f"ID: {victim_id}"
        else:
            victim_id = target
            display_name = f"ID: {victim_id}"

        # 1. Получаем СВЕЖИЕ данные лаборатории атакующего из БД
        infecter = await repo_biowar.get_info_user_lab(user_id)
        if isinstance(infecter, (list, tuple)):
            infecter = infecter[0] if infecter else {}

        if not infecter or not isinstance(infecter, dict):
            logging.error(f"[MF ERROR] Не удалось получить данные лабы user_id={user_id}")
            break

        ready_pathogens = infecter.get('ready_pathogens', 0) or 0

        # Остановка при отсутствии патогенов
        if ready_pathogens < 1:
            await status_msg.reply("⚠️ <b>Массовое заражение остановлено:</b> закончились патогены!")
            break

        victimer = await repo_biowar.get_info_user_lab(victim_id) if victim_id else None
        if isinstance(victimer, (list, tuple)):
            victimer = victimer[0] if victimer else {}

        if not victimer or not isinstance(victimer, dict):
            logging.warning(f"[MF SKIP] Пропуск цели {victim_id}: не найдены данные лабы")
            fail_cnt += 1
            continue

        # 2. ПРИНУДИТЕЛЬНОЕ СПИСАНИЕ В БД И ОБНОВЛЕНИЕ ЛОКАЛЬНОГО СЧЕТЧИКА
        try:
            await repo_biowar.subtract_pathogens(user_id, 1)
        except Exception as e:
            logging.error(f"[MF SUBTRACT ERROR]: {e}")

        total_spent_pathogens += 1
        new_ready_pathogens = max(0, ready_pathogens - 1)

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
            status_text = f"🔴 <b>ПРОМАХ!</b>"

        percent = int((idx / len(targets_on_page)) * 100)
        filled = int(percent // 10)
        bar = "▓" * filled + "░" * (10 - filled)

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
        except Exception:
            pass

        await asyncio.sleep(1.2)

    report = (
        f"☣️ <b>Итоги массового заражения (Стр. {page}):</b>\n\n"
        f"🎯 Обработано целей: <b>{idx_processed} / {len(targets_on_page)}</b>\n"
        f"🟢 Пробито целей: <b>{success_cnt}</b>\n"
        f"🔴 Не пробито: <b>{fail_cnt}</b>\n"
        f"🧪 Потрачено патогенов: <b>{total_spent_pathogens}</b>\n\n"
        f"📈 <b>Получено опыта:</b>\n"
        f"🧬 <b>+{total_exp:,} XP</b>"
    )
    await status_msg.edit_text(report, parse_mode="HTML")

import re
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from humanize import intcomma
from redis.asyncio import Redis

from core import func
from core.data.icons import LabIco
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()
logger = logging.getLogger(__name__)

class EpiLabAdminStates(StatesGroup):
    waiting_for_ac_reason = State()
    waiting_for_block_reason = State()
    waiting_for_transfer_target = State()

def parse_time_duration(text: str) -> tuple[int, int]:
    text = text.strip().lower()
    now_ts = int(datetime.utcnow().timestamp())
    if text in ['навсегда', 'forever', '0', 'perm', 'на вечно', 'всегда']:
        expire_ts = now_ts + (3650 * 24 * 3600)
        return expire_ts, (3650 * 24 * 3600)

    # Добавили 'ч' в список допустимых суффиксов
    match = re.match(r'^(\d+)([мmhhdдч]?)$', text)
    if not match:
        return now_ts + 3600, 3600

    val, unit = match.groups()
    val = int(val)

    if unit in ['м', 'm']:
        seconds = val * 60
    elif unit in ['ч', 'h']:
        seconds = val * 3600
    elif unit in ['д', 'd']:
        seconds = val * 86400
    else:
        seconds = val * 60

    return now_ts + seconds, seconds

async def resolve_lab_target(message: Message, query: str = None, repo_biowar: RequestsRepoBiowar = None):
    if message.reply_to_message and not query:
        replied_user = message.reply_to_message.from_user
        if replied_user:
            lab = await repo_biowar.get_info_user_lab(replied_user.id)
            if lab:
                return lab
            return {'id': replied_user.id}

    if not query:
        return None

    query = query.strip()
    if "user_id=" in query:
        match_uid = re.search(r'user_id=(\d+)', query)
        if match_uid:
            query = match_uid.group(1)

    target_user_id = None
    if query.isdigit():
        target_user_id = int(query)
    else:
        clean_query = query.lstrip('@')
        
        if hasattr(repo_biowar, 'get_id_by_username'):
            try:
                res = await repo_biowar.get_id_by_username(clean_query)
                if res:
                    target_user_id = res.get('user_id') or res.get('id') if isinstance(res, dict) else int(res)
            except Exception:
                pass

        if not target_user_id and hasattr(repo_biowar, 'get_user'):
            try:
                user = await repo_biowar.get_user(clean_query)
                if user:
                    target_user_id = user.get('user_id') or user.get('id')
            except Exception:
                pass

    if target_user_id:
        lab = await repo_biowar.get_info_user_lab(target_user_id)
        if lab:
            return lab
        return {'id': target_user_id}

    return None

@router.message(F.text.regexp(r'^!(?:эпилаб|epilab)(?:\s+(.*))?', flags=re.IGNORECASE))
async def cmd_epi_lab(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar):
    await state.clear()
    match = re.match(r'^!(?:эпилаб|epilab)(?:\s+(.*))?', message.text, re.IGNORECASE)
    query = match.group(1) if match else None

    lab_data = await resolve_lab_target(message, query, repo_biowar)
    if not lab_data or 'id' not in lab_data:
        await message.answer("⚠️ Использование: !эпилаб <user_id, @username> или реплаем на сообщение игрока.")
        return

    target_id = lab_data['id']

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔬 Просмотр лаборатории", callback_data=f"epilab:view:{target_id}")],
        [InlineKeyboardButton(text="⛔ АС (Мут команд)", callback_data=f"epilab:ac:{target_id}")],
        [InlineKeyboardButton(text="🔒 Запрет смены имени/патогена", callback_data=f"epilab:blockname:{target_id}")],
        [InlineKeyboardButton(text="🔓 Снять ограничения", callback_data=f"epilab:unblock:{target_id}")],
        [InlineKeyboardButton(text="🔄 Перенос лаборатории", callback_data=f"epilab:transfer:{target_id}")],
        [InlineKeyboardButton(text="💣 Обнул", callback_data=f"epilab:reset:{target_id}")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="epilab:close")]
    ])

    await message.answer(f"🎛 <b>Управление лабораторией:</b> <code>{target_id}</code>", reply_markup=kb)

@router.message(F.text.regexp(r'^!(?:асы|aclist|списокм)', flags=re.IGNORECASE))
async def cmd_list_aces(message: Message, repo_biowar: RequestsRepoBiowar):
    game_mutes = await repo_biowar.get_gamemute_list() if hasattr(repo_biowar, 'get_gamemute_list') else []
    bio_mutes = await repo_biowar.get_biomute_list() if hasattr(repo_biowar, 'get_biomute_list') else []

    text_lines = ["<b>📋 Список активных ограничений (АС и запретов):</b>\n"]

    if game_mutes:
        text_lines.append("<b>⛔ АС (Муты команд):</b>")
        for m in game_mutes:
            uid = m.get('user_id') or m.get('id')
            admin_id = m.get('admin_id', '?')
            reason = m.get('reason', 'не указана')
            expire = m.get('expire', 0)
            expire_str = datetime.utcfromtimestamp(expire).strftime('%Y-%m-%d %H:%M') if expire else 'навсегда'
            text_lines.append(f"• Игрок: <code>{uid}</code> | Админ: <code>{admin_id}</code>\n  Причина: {reason} | До: {expire_str}")
        text_lines.append("")

    if bio_mutes:
        text_lines.append("<b>🔒 Запреты смены имени/патогена:</b>")
        for m in bio_mutes:
            uid = m.get('user_id') or m.get('id')
            admin_id = m.get('admin_id', '?')
            reason = m.get('reason', 'не указана')
            expire = m.get('expire', 0)
            expire_str = datetime.utcfromtimestamp(expire).strftime('%Y-%m-%d %H:%M') if expire else 'навсегда'
            text_lines.append(f"• Игрок: <code>{uid}</code> | Админ: <code>{admin_id}</code>\n  Причина: {reason} | До: {expire_str}")

    if not game_mutes and not bio_mutes:
        text_lines.append("<i>Активных ограничений в базе данных не найдено.</i>")

    await message.answer("\n".join(text_lines), disable_web_page_preview=True)

@router.callback_query(F.data.startswith('epilab:'))
async def epilab_callback(callback: CallbackQuery, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis):
    parts = callback.data.split(':')
    action = parts[1]

    if action == 'close':
        await state.clear()
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.answer()
        return

    target_id = int(parts[2]) if len(parts) > 2 else None

    if action == 'view':
        lab_info = await repo_biowar.get_info_user_lab(target_id)
        corp_info = await repo_biowar.get_corporation(target_id)
        
        if not lab_info:
            return await callback.answer("Лаборатория не найдена!", show_alert=True)
            
        infected = await repo_biowar.get_my_infected(lab_info['id'])
        illnesses = await repo_biowar.get_my_illnesses(lab_info['id'])

        full_name = lab_info["full_name"]
        name_entity = func.entity_create_full_name(lab_info['id'], lab_info['full_name'])
        pathogen_name = lab_info["pathogen_name"] if lab_info["pathogen_name"] else 'засекречено'
        lab_name = lab_info['lab_name'] if lab_info['lab_name'] else full_name
        
        fever = func.fever_expire_difference_check(lab_info['fever']) if lab_info['fever'] else None
        if fever:
            fever = f"⏳ Лихорадка активна до: {fever}\n"
        
        fever_time = int(lab_info['lethality'] / 3)
        fever_time = (1 if fever_time == 0 else (60 if fever_time >= 180 else fever_time))
        
        refresh_pathogen_time = '\n'
        if lab_info["science_time"]:
            science_time = func.fever_expire_difference_check(lab_info["science_time"])
            refresh_pathogen_time = f'<i>{LabIco.sand_clock.value} Новый патоген через {science_time}</i>\n\n'
        
        if corp_info:
            corp_text = f'В составе Корпорации — «<a href="tg://openmessage?user_id={corp_info["leader_id"]}">{corp_info["name"]}</a>»\n\n'
        else:
            corp_text = '\n'
        
        custom_emoji = lab_info['customization_emoji'] if lab_info['customization_emoji'] else ''
        
        time_food = await repo_biowar.get_time_food()
        time_food_diff = datetime.utcfromtimestamp(time_food) - datetime.utcnow()
        get_food_text = func.convert_seconds_to_human(time_food_diff.total_seconds())
        
        lab_text = (
            f'<b>📩 Досье лаборатории {lab_name}:</b>\n'
            f'Руководитель — {name_entity} {custom_emoji}\n'
            f'{corp_text}'
            f'{LabIco.label.value} <b>Имя патогена:</b> {pathogen_name}\n'
            f'{LabIco.pathogens.value} <b>Готовых патогенов:</b> {lab_info["ready_pathogens"]}/{lab_info["pathogens"]}\n'
            f'{LabIco.science.value} <b>Квалификация учёных:</b> {lab_info["science"]} ур ({61 - lab_info["science"]} мин.)\n'
            f'{refresh_pathogen_time}'
            f'<blockquote><b>——[ Характеристика]——</b>\n'
            f'{LabIco.infect.value} Заразность: {lab_info["infect"]} ур\n'
            f'{LabIco.immunity.value} Иммунитет: {lab_info["immunity"]} ур\n'
            f'{LabIco.lethality.value} Летальность: {lab_info["lethality"]} ур ({fever_time} мин | {lab_info["lethality"]} дн)\n'
            f'{LabIco.security_service.value} Служба безопасности: {lab_info["security_service"]} ур</blockquote>\n'
            f'<b>ID лаборатории:</b> {lab_info["id"]}\n'
            '<b>——————————————</b>\n'
            '<blockquote><b>—[Запасы — реагентов]—</b>\n'
            f'{LabIco.bio_experience.value} Опыт: {intcomma(lab_info["bio_experience"]).replace(",", " ")}\n'
            f'{LabIco.bio_resource.value} Ресурсы: {intcomma(lab_info["bio_resource"]).replace(",", " ")}\n'
            f'{LabIco.time.value} <i>Ежедневная премия через: {get_food_text}</i>\n'
            f'{fever + "</blockquote>" if fever else "</blockquote>"}\n'
            f'{LabIco.infected.value} Заражённых: {infected}\n'
            f'{LabIco.illnesses.value} Своих болезней: {illnesses}\n'
        )
        
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к управлению", callback_data=f"epilab:main:{target_id}")]
        ])
        
        await callback.message.edit_text(lab_text, disable_web_page_preview=True, reply_markup=back_keyboard)
        await callback.answer()

    elif action == 'main':
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔬 Просмотр лаборатории", callback_data=f"epilab:view:{target_id}")],
            [InlineKeyboardButton(text="⛔ АС (Мут команд)", callback_data=f"epilab:ac:{target_id}")],
            [InlineKeyboardButton(text="🔒 Запрет смены имени/патогена", callback_data=f"epilab:blockname:{target_id}")],
            [InlineKeyboardButton(text="🔓 Снять ограничения", callback_data=f"epilab:unblock:{target_id}")],
            [InlineKeyboardButton(text="🔄 Перенос лаборатории", callback_data=f"epilab:transfer:{target_id}")],
            [InlineKeyboardButton(text="💣 Обнул", callback_data=f"epilab:reset:{target_id}")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="epilab:close")]
        ])
        await callback.message.edit_text(f"🎛 <b>Управление лабораторией:</b> <code>{target_id}</code>", reply_markup=back_kb)
        await callback.answer()

    elif action == 'ac':
        await state.update_data(target_id=target_id)
        await state.set_state(EpiLabAdminStates.waiting_for_ac_reason)
        await callback.message.answer("✍️ Введите причину и время для АС (например: <code>спам 10м</code> или <code>нарушение навсегда</code>):")
        await callback.answer()

    elif action == 'blockname':
        await state.update_data(target_id=target_id)
        await state.set_state(EpiLabAdminStates.waiting_for_block_reason)
        await callback.message.answer("✍️ Введите причину и время для запрета смены имени/патогена (например: <code>недопустимое имя 2ч</code>):")
        await callback.answer()

    elif action == 'unblock':
        await repo_biowar.game_mute_cancel(target_id)
        await repo_biowar.bio_mute_cancel(target_id)
        for prefix in ["epidemic_gamemute:", "gamemute:", "biomute:", "epidemic_biomute:"]:
            try:
                await redis.delete(f"{prefix}{target_id}")
            except Exception:
                pass
        await callback.answer(f"✅ Все ограничения и АС для {target_id} сняты!", show_alert=True)

    elif action == 'transfer':
        await state.update_data(target_id=target_id)
        await state.set_state(EpiLabAdminStates.waiting_for_transfer_target)
        await callback.message.answer("🔄 Введите <code>user_id</code>, <code>@username</code> или отправьте реплаем сообщение второго игрока для переноса лаборатории:")
        await callback.answer()

    elif action == 'reset':
        try:
            await repo_biowar.update_lab_skill_val(target_id, 'infect', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'immunity', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'lethality', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'security_service', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'science', 1)
            await repo_biowar.update_lab_skill_val(target_id, 'pathogens', 4)
            await repo_biowar.update_lab_skill_val(target_id, 'ready_pathogens', 0)
            await repo_biowar.update_lab_skill_val(target_id, 'bio_experience', 1000)
            await repo_biowar.update_lab_skill_val(target_id, 'bio_resource', 15000)
            
            await repo_biowar.pathogen_name_change(None, target_id)
            await repo_biowar.lab_name_change(None, target_id)
            
            db_obj = getattr(repo_biowar, 'pool', None)
            if not db_obj:
                for val in repo_biowar.__dict__.values():
                    if hasattr(val, 'acquire') or hasattr(val, 'execute'):
                        db_obj = val
                        break

            if db_obj and hasattr(db_obj, 'acquire'):
                async with db_obj.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            "UPDATE biowar_labs SET fever = NULL, science_time = NULL, cases = 0, coins = 500, case_1 = 0, case_2 = 0 WHERE id = %s", 
                            (target_id,)
                        )
                        await cursor.execute("DELETE FROM biowar_infected WHERE lab_id = %s OR target_id = %s", (target_id, target_id))
                        await conn.commit()
            elif hasattr(repo_biowar, 'execute'):
                await repo_biowar.execute(
                    "UPDATE biowar_labs SET fever = NULL, science_time = NULL, cases = 0, coins = 500, case_1 = 0, case_2 = 0 WHERE id = %s", 
                    (target_id,)
                )
                await repo_biowar.execute("DELETE FROM biowar_infected WHERE lab_id = %s OR target_id = %s", (target_id, target_id))

        except Exception as e:
            logger.exception(f"Error during lab reset for {target_id}: {e}")
            await callback.answer(f"❌ Ошибка обнуления: {e}", show_alert=True)
            return

        try:
            await redis.delete(f"epidemic_lab:{target_id}")
        except Exception:
            pass

        await callback.answer(f"✅ Лаборатория {target_id} обнулена!", show_alert=True)

@router.message(EpiLabAdminStates.waiting_for_ac_reason)
async def process_ac_input(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis):
    data = await state.get_data()
    target_id = int(data.get('target_id'))
    await state.clear()

    text = message.text.strip()
    parts = text.split()

    if len(parts) > 1 and re.match(r'^\d+[мmhhdдч]?$|^навсегда$|^forever$', parts[-1].lower()):
        time_str = parts[-1]
        reason = " ".join(parts[:-1])
    else:
        time_str = '1ч'
        reason = text

    expire_time, duration_seconds = parse_time_duration(time_str)
    
    await repo_biowar.game_mute(target_id, expire_time, message.from_user.id, reason)

    for prefix in ["epidemic_gamemute:", "gamemute:"]:
        try:
            await redis.set(f"{prefix}{target_id}", "1", ex=duration_seconds)
        except Exception:
            pass

    try:
        await message.bot.send_message(
            target_id,
            f"❌ Вы заблокированы на {time_str} по причине: {reason}"
        )
    except Exception:
        pass

    await message.answer(f"✅ Игроку <code>{target_id}</code> успешно выдан АС ({time_str}, причина: {reason})!")

@router.message(EpiLabAdminStates.waiting_for_block_reason)
async def process_block_input(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar, redis: Redis):
    data = await state.get_data()
    target_id = int(data.get('target_id'))
    await state.clear()

    text = message.text.strip()
    parts = text.split()

    if len(parts) > 1 and re.match(r'^\d+[мmhhdдч]?$|^навсегда$|^forever$', parts[-1].lower()):
        time_str = parts[-1]
        reason = " ".join(parts[:-1])
    else:
        time_str = '1ч'
        reason = text

    expire_time, duration_seconds = parse_time_duration(time_str)
    
    lab_info = await repo_biowar.get_info_user_lab(target_id)
    corp_info = await repo_biowar.get_corporation(target_id)
    lab_name = lab_info.get('lab_name') if lab_info else None
    
    await repo_biowar.bio_mute(target_id, lab_name, corp_info, expire_time, message.from_user.id, reason)

    for prefix in ["epidemic_biomute:", "biomute:"]:
        try:
            await redis.set(f"{prefix}{target_id}", "1", ex=duration_seconds)
        except Exception:
            pass

    try:
        await message.bot.send_message(
            target_id,
            f"🔒 Вам запрещено менять имя лаборатории и патогена на {time_str} по причине: {reason}"
        )
    except Exception:
        pass

    await message.answer(f"✅ Игроку <code>{target_id}</code> установлен запрет смены имени и патогена на {time_str}!")

@router.message(EpiLabAdminStates.waiting_for_transfer_target)
async def process_transfer_target(message: Message, state: FSMContext, repo_biowar: RequestsRepoBiowar):
    data = await state.get_data()
    source_id = int(data.get('target_id'))
    await state.clear()

    target_lab_data = await resolve_lab_target(message, message.text, repo_biowar)
    if not target_lab_data or 'id' not in target_lab_data:
        await message.answer("❌ Второй пользователь или лаборатория не найдены в базе данных.")
        return

    target_id = int(target_lab_data['id'])
    if source_id == target_id:
        await message.answer("⚠️ Нельзя перенести лабораторию на самого себя.")
        return

    lab_from = await repo_biowar.get_info_user_lab(source_id)
    lab_to = await repo_biowar.get_info_user_lab(target_id)
    bag_from = await repo_biowar.get_bag(source_id) if hasattr(repo_biowar, 'get_bag') else {}
    bag_to = await repo_biowar.get_bag(target_id) if hasattr(repo_biowar, 'get_bag') else {}
    pet_from = await repo_biowar.get_my_pet(source_id) if hasattr(repo_biowar, 'get_my_pet') else {}

    if not lab_from or not lab_to:
        await message.answer("❌ Одна из лабораторий не найдена в базе данных.")
        return

    try:
        await repo_biowar.lab_tranfer(lab_from, lab_to, bag_from, bag_to, pet_from)
        await message.answer(f"✅ Успешный перенос/обмен лаборатории между пользователями <code>{source_id}</code> и <code>{target_id}</code>!")
    except Exception as e:
        logger.exception(f"Error during lab transfer: {e}")
        await message.answer(f"❌ Ошибка при переносе лаборатории: {e}")

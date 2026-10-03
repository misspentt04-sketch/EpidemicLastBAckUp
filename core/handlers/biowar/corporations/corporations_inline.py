from aiogram import Bot
from aiogram.types import CallbackQuery

from aiogram.utils.markdown import hlink

from asyncmy.cursors import Cursor

from core.utils.callbackdata import Corporation
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

from core.data.tricks.tricks_biowar import tricks_biowar

from core import func

from humanize import intcomma


async def corporation_get_members(call: CallbackQuery, bot: Bot, callback_data: Corporation, db: Cursor, repo_biowar: RequestsRepoBiowar):

    id = call.from_user.id
    
    corp = await repo_biowar.get_corporation(corp_code=callback_data.corp_code)
    user = await repo_biowar.get_user(id)
    user_entity = hlink(user['full_name'], f'tg://user?id={user["id"]}')
    
    if id != callback_data.id and corp['corporation_dossier'] == 0:
        await call.message.answer(tricks_biowar['corporation']['corp_info_secret'].format(user_entity))
        return await call.answer()
    
    
    corp_members = await repo_biowar.get_corporation_members(corp['invitation_code'])
    corp_members_ = func.get_corp_members_or_invite_list(corp_members)
    
    text = (
        tricks_biowar['corporation']['get_corporation_members'].format(
            corp['name'],
            '\n'.join(corp_members_)
        )
    )
    
    await call.message.answer(tricks_biowar['text']['button_click_action'].format(user_entity))
    await call.message.answer(text)
    await call.answer()


async def invite_request_corporation_inline(call: CallbackQuery, bot: Bot, callback_data: Corporation, db: Cursor, repo_biowar: RequestsRepoBiowar):

    id = call.from_user.id
    corp_code = callback_data.corp_code
    corp = await repo_biowar.get_corporation(corp_code=corp_code)
    corp_me = await repo_biowar.get_corporation(id)
    
    user = await repo_biowar.get_user(id)
    user_entity = hlink(user['full_name'], f'tg://user?id={user["id"]}')
    
    if corp_me:
        await call.message.answer(tricks_biowar['corporation']['alredy_exists_corporation_inline'].format(
            user_entity,
            corp_me['invitation_code']))
        return await call.answer()
    elif not corp:
        await call.message.answer(tricks_biowar['corporation']['corporation_does_not_exists_inline'].format(user_entity))
        return await call.answer()
    
    count_labs = await repo_biowar.get_corporation_members_count(corp['invitation_code'])
    
    # Проверка лимита: 50 базовых + bonus_slots (до 100)
    base_slots = int(tricks_biowar['max']['corp_max_members'])  # 50
    max_slots = 100
    bonus = int(corp.get('bonus_slots') or 0) if isinstance(corp, dict) else 0
    allowed = min(base_slots + bonus, max_slots)

    if count_labs >= allowed:
        await call.message.answer(tricks_biowar['corporation']['member_limit_reached'])
        return await call.answer()
    
    invite_request = await repo_biowar.corp_check_invite_request(id, corp_code)
    
    if invite_request:
        await call.message.answer(tricks_biowar['corporation']['already_has_invite_request'])
        return await call.answer()
    
    invite_user = await repo_biowar.get_info_user_lab(id)
    
    await repo_biowar.send_invite_request_corporation(corp_code, id, call.from_user.full_name, invite_user['bio_experience'])
    
    text = (
        tricks_biowar['corporation']['invite_request_send_corp_inline'].format(user_entity, corp['name'])
    )
    
    await call.message.answer(text)

    # Уведомляем владельца + соруков в ЛС
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        notify_ids = set()
        if corp.get('leader_id'):
            notify_ids.add(int(corp['leader_id']))
        try:
            admins = await repo_biowar.get_corp_admin_list(corp_code)
            if admins:
                for a in admins:
                    # a — dict или int
                    if isinstance(a, dict):
                        mid = a.get('member_id') or a.get('id')
                    else:
                        mid = a
                    if mid:
                        notify_ids.add(int(mid))
        except Exception as e:
            print(f"[CORP NOTIFY ADMINS ERROR] {e}")

        notify_ids.discard(int(id))
        print(f"[CORP NOTIFY] notify_ids={notify_ids} corp_code={corp_code} leader={corp.get('leader_id')}")

        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Принять", callback_data=f"corp_accept_one:{corp_code}:{id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"corp_reject_one:{corp_code}:{id}"),
        ]])

        notify_text = (
            f"📩 <a href='tg://user?id={id}'>{call.from_user.full_name}</a> "
            f"хочет вступить в корпу <b>«{corp['name']}»</b>\n\n"
            f"⚡ Био-опыт: <code>{int(invite_user['bio_experience']):,}</code>"
        )

        for nid in notify_ids:
            try:
                await call.bot.send_message(
                    nid,
                    notify_text,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
                print(f"[CORP NOTIFY] отправлено {nid}")
            except Exception as e:
                print(f"[CORP NOTIFY ERROR] {nid}: {e}")
    except Exception as e:
        print(f"[CORP NOTIFY GLOBAL ERROR] {e}")

    await call.answer()


# ===== МАССОВОЕ ПРИНЯТИЕ / ОТКЛОНЕНИЕ =====

async def corp_accept_all(call: CallbackQuery, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    try:
        corp_code = call.data.split(":")[1]
    except (ValueError, IndexError):
        return await call.answer("❌ Ошибка", show_alert=True)

    corp = await repo_biowar.get_corporation(call.from_user.id)
    if not corp or corp['invitation_code'] != corp_code:
        return await call.answer("❌ Это не твоя корпа!", show_alert=True)
    if corp['is_admin'] == 0:
        return await call.answer("❌ Только для админов корпы!", show_alert=True)

    accepted = await repo_biowar.accept_all_corp_invites(corp_code)

    # Уведомляем принятых
    for uid in accepted:
        try:
            await bot.send_message(
                uid,
                f"🎉 Вас приняли в корпорацию <b>«{corp['name']}»</b>!\n\n"
                f"Используйте <code>.корп</code> для просмотра информации.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await call.message.edit_text(
        f"✅ Принято в корпу «{corp['name']}»: <b>{len(accepted)}</b>"
    )
    await call.answer(f"✅ Принято: {len(accepted)}")


async def corp_reject_all(call: CallbackQuery, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    try:
        corp_code = call.data.split(":")[1]
    except (ValueError, IndexError):
        return await call.answer("❌ Ошибка", show_alert=True)

    corp = await repo_biowar.get_corporation(call.from_user.id)
    if not corp or corp['invitation_code'] != corp_code:
        return await call.answer("❌ Это не твоя корпа!", show_alert=True)
    if corp['is_admin'] == 0:
        return await call.answer("❌ Только для админов корпы!", show_alert=True)

    rejected = await repo_biowar.reject_all_corp_invites(corp_code)

    for uid in rejected:
        try:
            await bot.send_message(
                uid,
                f"😔 Ваша заявка в корпорацию <b>«{corp['name']}»</b> отклонена.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await call.message.edit_text(
        f"❌ Отклонено заявок в корпу «{corp['name']}»: <b>{len(rejected)}</b>"
    )
    await call.answer(f"❌ Отклонено: {len(rejected)}")


# ===== Принятие/отклонение одной заявки =====

async def corp_accept_one(call: CallbackQuery, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    try:
        _, corp_code, uid = call.data.split(":")
        uid = int(uid)
    except (ValueError, IndexError):
        return await call.answer("❌ Ошибка", show_alert=True)

    corp = await repo_biowar.get_corporation(call.from_user.id)
    if not corp or corp['invitation_code'] != corp_code:
        return await call.answer("❌ Это не твоя корпа!", show_alert=True)
    if corp['is_admin'] == 0 and corp.get('leader_id') != call.from_user.id:
        return await call.answer("❌ Только для админов корпы!", show_alert=True)

    user = await repo_biowar.get_info_user_lab(uid)
    if not user:
        return await call.answer("❌ Игрок не найден", show_alert=True)

    infected = await repo_biowar.get_my_infected(uid)
    ok = await repo_biowar.claim_invite_request_corporation(
        corp_code, uid, user['full_name'], user['bio_experience'], infected
    )

    if not ok:
        return await call.answer("❌ Уже в корпе или лимит достигнут", show_alert=True)

    try:
        await call.message.edit_text(f"✅ Принят: {user['full_name']}")
    except Exception:
        pass

    try:
        await bot.send_message(
            uid,
            f"🎉 Вас приняли в корпорацию <b>«{corp['name']}»</b>!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.answer("Принят")


async def corp_reject_one(call: CallbackQuery, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    try:
        _, corp_code, uid = call.data.split(":")
        uid = int(uid)
    except (ValueError, IndexError):
        return await call.answer("❌ Ошибка", show_alert=True)

    corp = await repo_biowar.get_corporation(call.from_user.id)
    if not corp or corp['invitation_code'] != corp_code:
        return await call.answer("❌ Это не твоя корпа!", show_alert=True)
    if corp['is_admin'] == 0 and corp.get('leader_id') != call.from_user.id:
        return await call.answer("❌ Только для админов корпы!", show_alert=True)

    await repo_biowar.reject_invite_request_corporation(corp_code, uid)

    try:
        await call.message.edit_text(f"❌ Отклонён ID: {uid}")
    except Exception:
        pass

    try:
        await bot.send_message(
            uid,
            f"😔 Ваша заявка в корпорацию <b>«{corp['name']}»</b> отклонена.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await call.answer("Отклонён")


# ==================== CORPORATION: DOSSIER / TREASURY / LEVEL ====================

from core.data.corp_levels import CORP_LEVELS, MAX_CORP_LEVEL, exp_bonus_for_level
from core.keyboards.inline.corporation import corp_navigation, corp_upgrade_menu_kb, corp_treasury_menu_kb


async def corp_toggle_dossier(call: CallbackQuery, bot: Bot, callback_data: Corporation, db: Cursor, repo_biowar: RequestsRepoBiowar):
    id = call.from_user.id
    corp_me = await repo_biowar.get_corporation(id)
    if not corp_me:
        return await call.answer("Ты не в корпе", show_alert=True)
    corp = corp_me[0] if isinstance(corp_me, list) else corp_me
    if corp['invitation_code'] != callback_data.corp_code:
        return await call.answer("Это не твоя корпа", show_alert=True)

    # Проверка: владелец или сорук
    is_owner = (int(corp['leader_id']) == int(id))
    is_admin = False
    if not is_owner:
        member = await repo_biowar.select_all(
            'SELECT is_admin FROM CorporationMembers WHERE corporation_code=%s AND member_id=%s LIMIT 1;',
            (callback_data.corp_code, id),
            use_index_zero=False,
        )
        is_admin = bool(member and int(member[0].get('is_admin') or 0) == 1)

    if not (is_owner or is_admin):
        return await call.answer("❌ Только владелец или соруководитель", show_alert=True)

    new_state = await repo_biowar.corp_toggle_dossier(callback_data.corp_code)
    await call.answer("Открыто" if new_state else "Закрыто")


async def corp_treasury_menu(call: CallbackQuery, bot: Bot, callback_data: Corporation, db: Cursor, repo_biowar: RequestsRepoBiowar):
    id = call.from_user.id
    corp_me = await repo_biowar.get_corporation(id)
    if not corp_me:
        return await call.answer("Ты не в корпе", show_alert=True)
    corp = corp_me[0] if isinstance(corp_me, list) else corp_me
    if corp['invitation_code'] != callback_data.corp_code:
        return await call.answer("Это не твоя корпа", show_alert=True)

    info = await repo_biowar.corp_get_level_treasury(callback_data.corp_code)
    level = int(info.get('level') or 0)
    treasury = int(info.get('treasury') or 0)
    infected = int(info.get('infected') or 0)

    # Персональный вклад игрока
    my_deposited = await repo_biowar.corp_get_user_deposited(callback_data.corp_code, id)

    next_level = level + 1 if level < MAX_CORP_LEVEL else None

    parts = [
        f"💰 Казна корпы «{corp['name']}»",
        "",
        f"💵 В казне: <b>{intcomma(treasury)}</b>",
        f"👤 Ты вложил: <b>{intcomma(my_deposited)}</b>",
        f"⭐ Уровень: <b>{level} / {MAX_CORP_LEVEL}</b>",
        f"☠️ Заражений корпы: <b>{intcomma(infected)}</b>",
    ]

    if next_level and next_level in CORP_LEVELS:
        req = CORP_LEVELS[next_level]
        parts += [
            "",
            f"📈 До {next_level} уровня:",
            f"├ ☠️ {intcomma(req['infected'])} заражений",
            f"└ 💰 {intcomma(req['resources'])} ресурсов в казне",
        ]

    top = await repo_biowar.corp_get_top_depositors(callback_data.corp_code, limit=5)
    if top:
        parts += ["", "🏆 Топ вкладчиков:"]
        for i, row in enumerate(top, 1):
            try:
                u = await repo_biowar.get_user(row['user_id'])
                name = u['full_name'] if u else f"ID {row['user_id']}"
                entity = hlink(name, f'tg://user?id={row["user_id"]}')
            except Exception:
                entity = f"ID {row['user_id']}"
            parts.append(f"{i}. {entity} — <b>{intcomma(int(row['total']))}</b>")

    parts += ["", f"💡 Чтобы вложить — ответь числом на это сообщение.", "", f"<i>ID: {callback_data.corp_code}</i>"]

    await call.message.answer("\n".join(parts), parse_mode="HTML",
                              reply_markup=corp_treasury_menu_kb(id, callback_data.corp_code))
    await call.answer()


async def corp_upgrade_menu(call: CallbackQuery, bot: Bot, callback_data: Corporation, db: Cursor, repo_biowar: RequestsRepoBiowar):
    id = call.from_user.id
    corp_me = await repo_biowar.get_corporation(id)
    if not corp_me:
        return await call.answer("Ты не в корпе", show_alert=True)
    corp = corp_me[0] if isinstance(corp_me, list) else corp_me
    if corp['invitation_code'] != callback_data.corp_code:
        return await call.answer("Это не твоя корпа", show_alert=True)

    info = await repo_biowar.corp_get_level_treasury(callback_data.corp_code)
    level = int(info.get('level') or 0)
    treasury = int(info.get('treasury') or 0)
    infected = int(info.get('infected') or 0)

    is_owner = (int(corp['leader_id']) == int(id))
    next_level = level + 1 if level < MAX_CORP_LEVEL else None

    bonus_pct = exp_bonus_for_level(level)
    is_max = (level >= MAX_CORP_LEVEL)

    header_level = "MAX" if is_max else f"{level}/{MAX_CORP_LEVEL}"

    parts = [
        f"👑 <b>{corp['name']}</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"⭐ Уровень: <b>{level}/{MAX_CORP_LEVEL}</b> · <b>{header_level}</b>",
        f"📦 Бонус: <b>+{bonus_pct}%</b> к ресурсам",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    if is_max:
        parts += [
            "",
            "✨ <b>Максимальный буст активирован!</b>",
            "🏆 <i>Корпа достигла предела развития.</i>",
        ]
    elif next_level and next_level in CORP_LEVELS:
        req = CORP_LEVELS[next_level]
        rtype, rvalue = req['reward']
        reward_text = {
            'resources': f"<b>{intcomma(rvalue)}</b> ресурсов каждому",
            'exp': f"<b>+{rvalue}%</b> ресурсов с жертв",
            'epicoins': f"<b>{intcomma(rvalue)}</b> эпикоинов каждому",
        }.get(rtype, str(rvalue))

        # Прогресс по заражениям
        need_inf = req['infected']
        inf_ok = "✅" if infected >= need_inf else "⏳"
        # Прогресс по ресурсам
        need_res = req['resources']
        res_ok = "✅" if treasury >= need_res else "⏳"

        parts += [
            "",
            f"📈 <b>До уровня {next_level}:</b>",
            "",
            f"{inf_ok} ☠️ Заражения:",
            f"   <code>{intcomma(infected)}</code> / <code>{intcomma(need_inf)}</code>",
            "",
            f"{res_ok} 💰 Ресурсы в казне:",
            f"   <code>{intcomma(treasury)}</code> / <code>{intcomma(need_res)}</code>",
            "",
            f"🎁 Награда: {reward_text}",
        ]

    if not is_owner:
        parts += ["", "⚠️ Прокачивать может только владелец корпы."]

    can_upgrade = bool(is_owner and next_level)
    await call.message.answer("\n".join(parts), parse_mode="HTML",
                              reply_markup=corp_upgrade_menu_kb(id, callback_data.corp_code, can_upgrade=can_upgrade))
    await call.answer()


async def corp_upgrade_confirm(call: CallbackQuery, bot: Bot, callback_data: Corporation, db: Cursor, repo_biowar: RequestsRepoBiowar):
    id = call.from_user.id
    corp_me = await repo_biowar.get_corporation(id)
    if not corp_me:
        return await call.answer("Ты не в корпе", show_alert=True)
    corp = corp_me[0] if isinstance(corp_me, list) else corp_me
    if corp['invitation_code'] != callback_data.corp_code:
        return await call.answer("Это не твоя корпа", show_alert=True)
    if int(corp['leader_id']) != int(id):
        return await call.answer("Только владелец может прокачивать", show_alert=True)

    info = await repo_biowar.corp_get_level_treasury(callback_data.corp_code)
    level = int(info.get('level') or 0)
    treasury = int(info.get('treasury') or 0)
    infected = int(info.get('infected') or 0)

    if level >= MAX_CORP_LEVEL:
        return await call.answer("Максимум достигнут", show_alert=True)

    next_level = level + 1
    req = CORP_LEVELS[next_level]

    if infected < req['infected']:
        return await call.answer(
            f"Нужно {intcomma(req['infected'])} заражений, у вас {intcomma(infected)}",
            show_alert=True,
        )
    if treasury < req['resources']:
        return await call.answer(
            f"Нужно {intcomma(req['resources'])} в казне, у вас {intcomma(treasury)}",
            show_alert=True,
        )

    await repo_biowar.corp_upgrade_level(
        callback_data.corp_code, next_level, id, req['infected'], req['resources'],
    )

    rtype, rvalue = req['reward']
    member_ids = await repo_biowar.corp_get_member_ids(callback_data.corp_code)

    if rtype == 'resources':
        for uid in member_ids:
            try:
                await repo_biowar.corp_reward_resources(uid, rvalue)
            except Exception as e:
                print(f"[CORP REWARD RES ERROR] {uid}: {e}")
    elif rtype == 'epicoins':
        for uid in member_ids:
            try:
                await repo_biowar.corp_reward_epicoins(uid, rvalue)
            except Exception as e:
                print(f"[CORP REWARD COIN ERROR] {uid}: {e}")

    notify = f"🎉 Корпа «{corp['name']}» прокачана до {next_level} уровня!"
    for uid in member_ids:
        try:
            await bot.send_message(uid, notify)
        except Exception:
            pass

    await call.message.answer(
        f"✅ Корпа прокачана до <b>{next_level}</b> уровня!\n"
        f"Осталось в казне: <b>{intcomma(treasury - req['resources'])}</b>",
        parse_mode="HTML",
    )
    await call.answer("Готово")


async def corp_back_to_main(call: CallbackQuery, bot: Bot, callback_data: Corporation, db: Cursor, repo_biowar: RequestsRepoBiowar):
    id = call.from_user.id
    corp_me = await repo_biowar.get_corporation(id)
    if not corp_me:
        return await call.answer("Не найдено", show_alert=True)
    corp = corp_me[0] if isinstance(corp_me, list) else corp_me

    # Проверка: владелец или сорук
    is_owner = (int(corp['leader_id']) == int(id))
    is_admin = False
    if not is_owner:
        _m = await repo_biowar.select_all(
            'SELECT is_admin FROM CorporationMembers WHERE corporation_code=%s AND member_id=%s LIMIT 1;',
            (callback_data.corp_code, id),
            use_index_zero=False,
        )
        is_admin = bool(_m and int(_m[0].get('is_admin') or 0) == 1)
    can_dossier = is_owner or is_admin

    await call.message.answer(
        "Главное меню корпы. Используй .корп для полного экрана.",
        reply_markup=corp_navigation(
            id, callback_data.corp_code,
            dossier_open=(corp['corporation_dossier'] == 1),
            is_member=True,
            can_dossier=can_dossier,
        ),
    )
    await call.answer()


async def corp_get_invites_callback(call: CallbackQuery, bot: Bot, callback_data: Corporation,
                                    db: Cursor, repo_biowar: RequestsRepoBiowar):
    """Callback-версия .корп заявки — по кнопке 📋 Заявки."""
    id = call.from_user.id

    corp = await repo_biowar.get_corporation(id)
    if not corp:
        return await call.answer("Ты не в корпе", show_alert=True)
    corp = corp[0] if isinstance(corp, list) else corp

    if corp['invitation_code'] != callback_data.corp_code:
        return await call.answer("Это не твоя корпа", show_alert=True)
    if corp['is_admin'] == 0 and int(corp['leader_id']) != int(id):
        return await call.answer("Только для админов корпы", show_alert=True)

    invite_list = await repo_biowar.get_active_corp_invite_list(corp['invitation_code'])
    invite_list = func.get_corp_members_or_invite_list(invite_list, 'invites')

    text = (
        tricks_biowar['corporation']['get_corporation_invites'].format(
            corp['name'],
            '\n'.join(invite_list) if invite_list else 'Нет активных заявок'
        )
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять всех", callback_data=f"corp_accept_all:{corp['invitation_code']}"),
        InlineKeyboardButton(text="❌ Отклонить всех", callback_data=f"corp_reject_all:{corp['invitation_code']}"),
    ]])

    await call.message.answer(text, reply_markup=kb)
    await call.answer()

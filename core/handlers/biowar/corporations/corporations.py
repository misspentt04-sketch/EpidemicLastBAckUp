from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from aiogram.utils.markdown import hlink

from core.keyboards.inline.corporation import corp_navigation
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core.data.icons import LabIco, OtherIco
from core.data.tricks.tricks_biowar import tricks_biowar

from core import func

from humanize import intcomma
from datetime import datetime

async def get_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    corp_code = None
    
    if len(msgt.split(' ')) >= 2:
        corp_code = msgt.split(' ')[-1]
        corp = await repo_biowar.get_corporation(corp_code=corp_code)
    else:
        corp = await repo_biowar.get_corporation(id)
    
    user = await repo_biowar.get_user(id)
    user_entity = hlink(user['full_name'], f'tg://user?id={user["id"]}')
    
    if not corp and corp_code:
        return await msg.answer(tricks_biowar['corporation']['corporation_does_not_exists'])
    elif not corp and not corp_code:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_corp'])
    elif corp_code and corp['corporation_dossier'] == 0:
        return await msg.answer(tricks_biowar['corporation']['corp_info_secret'].format(user_entity))
    
    count_labs = await repo_biowar.get_corporation_members_count(corp['invitation_code'])
    corp_leader = await repo_biowar.get_info_user_lab(corp['leader_id'])
    
    corp_leader_entity = func.entity_create_full_name(
        corp_leader['id'], corp_leader['full_name']
    )
    
    text = (
        tricks_biowar['corporation']['get_corporation'].format(
            corp['name'], corp_leader_entity, intcomma(corp['bio_experience']), corp['infected'],
            intcomma(corp['bio_experience']), corp['infected'], count_labs, corp['invitation_code'],
            ('открыто' if corp['corporation_dossier'] == 1 else 'засекречено')
        )
    )
    
    await msg.answer(text, reply_markup=corp_navigation(id, corp['invitation_code']))

async def create_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    corp_name = ' '.join(msgt.split(' ')[2:])
    corp = await repo_biowar.get_corporation(id)
    bio_mute = await repo_biowar.get_user_bio_mute(id)
    
    # errors
    if bio_mute:
        bio_mute_days = (datetime.fromtimestamp(bio_mute['time_expire']) - datetime.utcnow()).days
        return await msg.answer(tricks_biowar['epidemic_admins']['bio_muted'].format(bio_mute_days))
    if corp:
        return await msg.answer(tricks_biowar['corporation']['alredy_exists_corporation'].format(corp['invitation_code']))
    corp_name_check = await repo_biowar.select_all('SELECT name FROM Corporation WHERE name=%s;', corp_name)
    if corp_name_check:
        return await msg.answer(tricks_biowar['corporation']['corp_name_already_exists'])
    
    # не реализована система дупликатов corp code
    corp_code = func.corp_code_generator()
    lab_info = await repo_biowar.get_info_user_lab(id)
    infected = await repo_biowar.get_my_infected(id)

    text = (
        tricks_biowar['corporation']['create_corporation'].format(
            corp_name, corp_code
        )
    )
    
    await repo_biowar.create_corporation(
        id, corp_name, lab_info['full_name'],
        lab_info['bio_experience'], infected,
        corp_code
    )
    
    await msg.answer(text)

async def delete_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    corp = await repo_biowar.get_corporation(id)
    
    if not corp:
        return await msg.answer(tricks_biowar['corporation']['you_has_no_corp'])
    if not await repo_biowar.check_if_owner_corporation(corp['invitation_code'], id):
        return await msg.answer(tricks_biowar['corporation']['owner_cant_leave_from_own_corp'])
    
    text = tricks_biowar['corporation']['delete_corporation'].format(corp['name'])
    
    await repo_biowar.delete_corporation(corp['invitation_code'])
    
    await msg.answer(text)

async def invite_request_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    corp_code = msgt.split(' ')[-1]
    
    corp = await repo_biowar.get_corporation(corp_code=corp_code)
    corp_me = await repo_biowar.get_corporation(id)
    
    if corp_me:
        return await msg.answer(tricks_biowar['corporation']['alredy_exists_corporation'].format(corp_me['invitation_code']))
    if not corp:
        return await msg.answer(tricks_biowar['corporation']['corporation_does_not_exists'])
    
    count_labs = await repo_biowar.get_corporation_members_count(corp['invitation_code'])
    
    if count_labs >= tricks_biowar['max']['corp_max_members']:
        return await msg.answer(tricks_biowar['corporation']['member_limit_reached'])
    
    invite_request = await repo_biowar.corp_check_invite_request(id, corp_code)
    
    if invite_request:
        return await msg.answer(tricks_biowar['corporation']['already_has_invite_request'])
    
    invite_user = await repo_biowar.get_info_user_lab(id)
    user = await repo_biowar.get_user(id)
    user_entity = func.entity_create_consider_username(user)
    
    await repo_biowar.send_invite_request_corporation(corp_code, id, msg.from_user.full_name, invite_user['bio_experience'])
    
    text = (
        tricks_biowar['corporation']['invite_request_send_corp'].format(user_entity, corp['name'])
    )
    
    await msg.answer(text)


async def invite_accept_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    invite_user = await repo_biowar.get_info_user_lab(func.reply_or_tag_geeter(msg))
    
    if invite_user == id:
        return
    
    corp = await repo_biowar.get_corporation(id)
    invite_user_corp = await repo_biowar.get_corporation(invite_user['id'])
    
    
    if not corp:
        return await msg.answer(tricks_biowar['corporation']['you_has_no_corp'])
    if corp['is_admin'] == 0:
        return await msg.answer(tricks_biowar['corporation']['you_are_not_admin'])
    
    invite_request = await repo_biowar.corp_check_invite_request(invite_user['id'], corp['invitation_code'])
    
    if not invite_request:
        return await msg.answer(tricks_biowar['corporation']['user_does_not_send_invite'])
    if invite_user_corp:
        return await msg.answer(tricks_biowar['corporation']['already_has_corp'])
    
    inv_user_infected = await repo_biowar.get_my_infected(invite_user['id'])

    mention = func.entity_create(invite_user['full_name'], invite_user['id'])
    
    await repo_biowar.claim_invite_request_corporation(
        corp['invitation_code'], invite_user['id'], invite_user['full_name'],
        invite_user['bio_experience'], inv_user_infected)
    
    await msg.answer(tricks_biowar['corporation']['invite_request_accept'].format(mention))
    try:
        await bot.send_message(tricks_biowar['corporation']['invite_reuqest_accept_pm_mention'].format(
            corp['name']
        ))
    except:
        pass

async def invite_reject_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    invite_user = await repo_biowar.get_info_user_lab(func.reply_or_tag_geeter(msg))
    
    if invite_user == id:
        return
    
    corp = await repo_biowar.get_corporation(id)
    
    invite_request = await repo_biowar.corp_check_invite_request(invite_user['id'], corp['invitation_code'])

    if corp['is_admin'] == 0:
        return await msg.answer(tricks_biowar['corporation']['you_are_not_admin'])
    if not invite_request:
        return await msg.answer(tricks_biowar['corporation']['user_does_not_send_invite'])
    
    await repo_biowar.reject_invite_request_corporation(corp['invitation_code'], invite_user['id'])
    
    await msg.answer(tricks_biowar['corporation']['invite_request_reject'])


async def get_corporation_members(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    corp_code = None
    
    if len(msgt.split(' ')) >= 3:
        corp_code = msgt.split(' ')[-1]
        corp = await repo_biowar.get_corporation(corp_code=corp_code)
    else:
        corp = await repo_biowar.get_corporation(id)
    
    user = await repo_biowar.get_user(id)
    user_entity = hlink(user['full_name'], f'tg://user?id={user["id"]}')
    
    if not corp and corp_code:
        return await msg.answer(tricks_biowar['corporation']['corporation_does_not_exists'])
    elif not corp and not corp_code:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_corp'])
    elif corp_code and corp['corporation_dossier'] == 0:
        return await msg.answer(tricks_biowar['corporation']['corp_info_secret'].format(user_entity))
    
    corp_members = await repo_biowar.get_corporation_members(corp['invitation_code'])
    corp_members_ = func.get_corp_members_or_invite_list(corp_members)
    
    text = (
        tricks_biowar['corporation']['get_corporation_members'].format(
            corp['name'],
            '\n'.join(corp_members_)
        )
    )
    
    await msg.answer(text)


async def leave_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    corp = await repo_biowar.get_corporation(id)
    
    if not corp:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_corp'])
    if await repo_biowar.check_if_owner_corporation(corp['invitation_code'], id):
        return await msg.answer(tricks_biowar['corporation']['owner_cant_leave_from_own_corp'])
    
    text = tricks_biowar['corporation']['leave_corp'].format(corp['name'])
    
    await repo_biowar.leave_corporation(corp['invitation_code'], id)
    
    await msg.answer(text)


async def kick_from_corporation(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    invite_user = await repo_biowar.get_info_user_lab(func.reply_or_tag_geeter(msg))
    corp = await repo_biowar.get_corporation(id)
    
    if not corp:
        return await msg.answer(tricks_biowar['corporation']['you_has_no_corp'])
    if corp['is_admin'] == 0:
        return await msg.answer(tricks_biowar['corporation']['you_are_not_admin'])
    
    is_corp_owner = await repo_biowar.check_if_owner_corporation(corp['invitation_code'], id)

    if invite_user['id'] == id and is_corp_owner:
        return await msg.answer(tricks_biowar['corporation']['owner_corp_self_kick'])

    corp_members_id = await repo_biowar.get_corporation_members_ids_list(corp['invitation_code'])
    
    if invite_user['id'] not in corp_members_id:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_your_corp'])
    
    admin_list = await repo_biowar.get_corp_admin_list(corp['invitation_code'])
    
    if invite_user['id'] in admin_list and not is_corp_owner or invite_user['id'] == corp['leader_id']:
        return await msg.answer(tricks_biowar['corporation']['admin_kick_restricted'])
    
    invite_user_entity = func.entity_create_full_name(
        invite_user['id'], invite_user['full_name']
    )
    corp_leader_entity = func.entity_create_full_name(
        invite_user['id'], corp['name']
    )
    
    text = tricks_biowar['corporation']['kick_from_corp'].format(invite_user_entity, corp_leader_entity)
    
    await repo_biowar.leave_corporation(corp['invitation_code'], invite_user['id'])
    
    await msg.answer(text)


async def get_corporation_invites(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    corp = await repo_biowar.get_corporation(id)
    
    if not corp:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_corp'])
    if corp['is_admin'] == 0:
        return await msg.answer(tricks_biowar['corporation']['you_are_not_admin'])
    
    invite_list = await repo_biowar.get_corp_invite_list(corp['invitation_code'])
    invite_list = func.get_corp_members_or_invite_list(invite_list, 'invites')
    
    
    text = (
        tricks_biowar['corporation']['get_corporation_invites'].format(
            corp['name'],
            '\n'.join(invite_list)
        )
    )
    
    await msg.answer(text)


async def change_corporation_name(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    corp_name = ' '.join(msgt.split(' ')[2:])
    corp = await repo_biowar.get_corporation(id)
    bio_mute = await repo_biowar.get_user_bio_mute(id)
    
    # errors
    if bio_mute:
        bio_mute_days = (datetime.fromtimestamp(bio_mute['time_expire']) - datetime.utcnow()).days
        return await msg.answer(tricks_biowar['epidemic_admins']['bio_muted'].format(bio_mute_days))
    if not corp:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_corp'])
    if corp['is_admin'] == 0:
        return await msg.answer(tricks_biowar['corporation']['you_are_not_admin'])
    
    await repo_biowar.change_corp_name(corp['invitation_code'], corp_name)
    
    text = tricks_biowar['corporation']['change_corp_name'].format(corp_name)
    
    await msg.answer(text)


async def deladd_corporation_admin(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    admin_id = await repo_biowar.get_id_by_username(func.reply_or_tag_geeter(msg))
    
    if admin_id == id:
        return
    
    admin = await repo_biowar.get_info_user_lab(admin_id)
    corp = await repo_biowar.get_corporation(id)
    bio_mute = await repo_biowar.get_user_bio_mute(id)
    
    # errors
    if bio_mute and msgt[0] == '+':
        bio_mute_days = (datetime.fromtimestamp(bio_mute['time_expire']) - datetime.utcnow()).days
        return await msg.answer(tricks_biowar['epidemic_admins']['bio_muted'].format(bio_mute_days))
    if not corp or not await repo_biowar.check_if_owner_corporation(corp['invitation_code'], id):
        return await msg.answer(tricks_biowar['corporation']['you_has_no_corp'])
    
    corp_members_id = await repo_biowar.get_corporation_members_ids_list(corp['invitation_code'])
    
    if admin_id not in corp_members_id:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_your_corp'])
    
    admin_corp = await repo_biowar.get_corporation(admin_id)
    
    if not admin_corp:
        return await msg.answer(tricks_biowar['corporation']['lab_not_in_your_corp'])
    
    corp_admin_entity = func.entity_create_full_name(
        admin_id, admin['full_name']
    )
    
    if msgt[0] == '+' and admin_corp['is_admin'] == 1:
        return await msg.answer(tricks_biowar['corporation']['already_corp_admin'].format(corp_admin_entity))
    elif msgt[0] == '-' and admin_corp['is_admin'] == 0:
        return await msg.answer(tricks_biowar['corporation']['isnt_corp_admin'].format(corp_admin_entity))
    
    if msgt[0] == '+':
        val = 1
        text = tricks_biowar['corporation']['add_corp_admin'].format(corp_admin_entity)
    else:
        val = 0
        text = tricks_biowar['corporation']['del_corp_admin'].format(corp_admin_entity)
    
    await repo_biowar.update_corp_admin(admin_id, corp['invitation_code'], val)
    
    await msg.answer(text)
    
async def get_corporation_admins(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    corp = await repo_biowar.get_corporation(id)
    
    if not corp or not await repo_biowar.check_if_owner_corporation(corp['invitation_code'], id):
        return await msg.answer(tricks_biowar['corporation']['you_has_no_corp'])
    
    admins_list = await repo_biowar.get_corp_admin_list(corp['invitation_code'])
    
    admins_list = func.get_corp_admins_list(admins_list)
    
    text = (
        tricks_biowar['corporation']['list_corp_admins'].format(
            corp['name'],
            '\n'.join(admins_list)
        )
    )
    
    await msg.answer(text)


async def corporation_dossier(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    corp = await repo_biowar.get_corporation(id)
    
    if not corp or not await repo_biowar.check_if_owner_corporation(corp['invitation_code'], id):
        return await msg.answer(tricks_biowar['corporation']['you_has_no_corp'])
    
    if msgt[0] == '+':
        val = 1
        text = tricks_biowar['corporation']['show_corp_dossier']
    else:
        val = 0
        text = tricks_biowar['corporation']['hide_corp_dossier']
    
    await repo_biowar.update_corp_dossier(corp['invitation_code'], val)
    
    await msg.answer(text)


async def get_corporations_biotop(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    biotop_corp = await repo_biowar.get_biotop_corps()
    
    biotop_corp_list = func.get_biotop_corp(biotop_corp)
    
    text = (
        tricks_biowar['biotops']['corporations'].format(
            '\n'.join(biotop_corp_list)
        )
    )
    
    await msg.answer(text)
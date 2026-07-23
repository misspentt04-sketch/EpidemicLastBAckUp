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
    
    if count_labs >= tricks_biowar['max']['corp_max_members']:
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
    await call.answer()

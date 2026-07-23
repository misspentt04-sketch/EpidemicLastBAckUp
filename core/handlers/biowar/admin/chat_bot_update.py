from aiogram.types import Message, ChatMemberUpdated
from asyncmy.cursors import Cursor
from aiogram import Bot, html, enums

from aiogram.types.chat_invite_link import ChatInviteLink
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

from core.data.texttriggers import deep_links
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.settings import settings, CHAT_LOGS
from core import func
from core.data.tg_ban_words import words as tg_ban_words
# # from core.handlers.chat_manage.marriages import # devorce_marriage_if_leave

# # from core.handlers.chat_manage.marriages.marriages import # devorce_marriage_if_leave


import logging

async def bot_added_to_group(event: ChatMemberUpdated, bot: Bot):
    
    get_chat = await bot.get_chat(event.chat.id)
    
    if get_chat.username:
        chat_entity = func.entity_create(get_chat.username, html.quote(event.chat.title), entity=deep_links['link'])
    else:
        chat_link = event.chat.id
        chat_entity = func.entity_create(chat_link, html.quote(event.chat.title))
    
    text = tricks_cm['chat_update']['bot_join_chat'].format(chat_entity)
    owner = func.entity_create(event.from_user.id, html.quote(event.from_user.full_name))
    
    await event.answer(text)
    try:
        await bot.send_message(
            chat_id=CHAT_LOGS,
            text=f'✨ Бот добавлен в новый чат {chat_entity} владелец {owner}'
        )
    except Exception as e:
        logging.warning(f"Bot can't send message to admin chat \t{e}")

# bad idea with us database structure
# async def group_to_supegroup_migration(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage):
#     await bot.send_message(
#         msg.migrate_to_chat_id,
#         'Чат обновлен в супергруппу\n'
#         f'Старый чат ID: <code>{(msg.chat.id)}</code>\n'
#         f'Новый чат ID: <code>{(msg.migrate_to_chat_id)}</code>'
#     )
#     await repo_cm.chat_migrate_to_supergroup(msg.chat.id, msg.migrate_to_chat_id)

async def new_chat_member(
        event: ChatMemberUpdated,
        bot: Bot,
        db: Cursor,
        repo_cm: RequestsRepoChatManage,
        repo_biowar: RequestsRepoBiowar
):
    chat_id = event.chat.id

    if event.new_chat_member:
        user = event.new_chat_member.user
    else:
        user = event.from_user
    
    clear_name = func.clear_name_universal(user.full_name.title(), user.username, user.id)
    await repo_biowar.add_data_user(user.id, clear_name, user.username)

    get = await repo_cm.get_regime_notifications(chat_id)

    if get['new_chat_member'] == 0:
        entity =  func.entity_create_consider_username(
            user_id=user.id, username=user.username, name=clear_name.title()
        )
        text = tricks_cm['chat_update']['join_chat'].format(entity)

        await event.answer(text, disable_web_page_preview=True)


async def leave_chat_member(
        event: ChatMemberUpdated,
        bot: Bot,
        db: Cursor,
        repo_cm: RequestsRepoChatManage,
        repo_biowar: RequestsRepoBiowar
):
    chat_id = event.chat.id

    if event.new_chat_member:
        user = event.new_chat_member.user
    else:
        user = event.from_user
        # await # devorce_marriage_if_leave(msg, bot, db, repo_cm, repo_biowar)

    get = await repo_cm.get_regime_notifications(chat_id)
    await repo_cm.delete_chat_member(user.id, chat_id)

    if get['leave_chat_member'] == 0:
        entity = func.entity_create_consider_username(
            user_id=user.id, username=user.username, name=func.clear_name_universal(user.full_name.title(), user.username, user.id)
        )
        text = tricks_cm['chat_update']['leave_chat'].format(entity)

        await event.answer(text, disable_web_page_preview=True)

async def upd_chat_name(
        msg: Message,
        repo_biowar: RequestsRepoBiowar
):
    chat_id = msg.chat.id
    chat_title = msg.chat.title

    await repo_biowar.update_chat_title(chat_id=chat_id, new_title=chat_title)
from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage

from core.data.tricks.tricks_chat_manage import tricks_cm
from core import func

async def get_admin(msg: Message, bot: Bot, db: Cursor, repo_cm: RequestsRepoChatManage, repo_biowar: RequestsRepoBiowar):
    
    chat_id = msg.chat.id

    result = await func.get_admins_chat(bot, chat_id)
    admin_ids = [member.user.id for member in result]
    admin_names = [member.user.full_name for member in result]

    await repo_cm.add_admins(chat_id=chat_id, admin_names=admin_names, admin_ids=admin_ids)
    admin_chat_members = await repo_cm.get_admins(chat_id)

    if not admin_chat_members:
        return await msg.answer(tricks_cm['admins']['admins_not_found'])
    
    admins_info = await repo_cm.get_admins_info_list(chat_id)
    
    admins_list = await func.get_admins_list(admins_info, chat_id)

    answer_text = tricks_cm['admins']['admin_list'].format('\n'.join(admins_list[0]))
    await msg.answer(answer_text)
from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.data.tricks.tricks_biowar import Const

from core import func

import random

async def rp_handler(msg: Message, repo_biowar: RequestsRepoBiowar, repo_cm: RequestsRepoChatManage):
    
    user_id = msg.from_user.id
    receiver_user = func.reply_or_tag_geeter(msg)
    rp = msg.text.lower().replace('.', '').replace('/', '').replace('!', '').split()[0]
    comment = ' '.join(msg.text.split()[2:] if func.link_getter(msg.text) else msg.text.split()[1:])
    if len(comment) >= 1:
        comment = Const.COMMENT_RP.format(comment)
    is_tag = func.check_if_tag(msg)
    
    sender_user = await repo_biowar.get_user(user_id)
    receiver_user = await repo_biowar.get_user(receiver_user)

    # errors
    if not is_tag and not msg.reply_to_message:
        return

    if not receiver_user:
        try:
            reply_user = msg.reply_to_message.from_user
            receiver_mention = func.entity_create_consider_username(
                user_id=reply_user.id,
                name=func.clear_name_universal(reply_user.full_name, reply_user.username, reply_user.id),
                username=reply_user.username
            )
        except:
            return
    else:
        receiver_mention = func.entity_create_consider_username(receiver_user)

    sender_mention = func.entity_create_consider_username(sender_user)

    text = random.choice(tricks_cm['rp'][rp.splitlines()[0].lower()]).format(sender_mention, receiver_mention)
    text += f'\n\n{comment}'

    await msg.answer(text, disable_web_page_preview=True)



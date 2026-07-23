from aiogram.types import Message

from core.data.tricks.tricks_chat_manage import tricks_cm

import re


async def bot_pm(msg: Message):
    
    if re.fullmatch(r'([./!]|)эпилс', msg.text, re.IGNORECASE):
        text = tricks_cm['start']['bot_pm']
    else:
        cmd_clean = '+'.join(msg.text.split()[1:]).replace('+', '%2B').replace('=', '%3D')
        cmd = ' '.join(msg.text.split()[1:])
        text = tricks_cm['start']['bot_pm_cmd'].format(cmd_clean, cmd)
    
    await msg.answer(text, disable_web_page_preview=True)


    
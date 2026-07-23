from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.utils.callbackdata import Corporation
from core.data.icons import LabIco


def corp_navigation(id: int, corp_code: str):
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Участники', callback_data=Corporation(id=id, action='corp_get_members', corp_code=corp_code))
    kb.button(text='Вступить', callback_data=Corporation(id=id, action='invite_request_corporation', corp_code=corp_code))
    
    kb.adjust(2),
    return kb.as_markup(resize_keyboard=True)

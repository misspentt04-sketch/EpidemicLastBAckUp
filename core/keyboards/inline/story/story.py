from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.utils.callbackdata import StoryStartAction
from core.data.icons import LabIco


def story_start_action(id: int):
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Начать путешествие', callback_data=StoryStartAction(id=id, action='story_start_action_'))
    
    return kb.as_markup(resize_keyboard=True)

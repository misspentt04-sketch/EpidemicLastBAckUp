from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.utils.callbackdata import Tutorial


def start_action():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='💚 Начать путешествие', callback_data=Tutorial(action='continue_1', lvl=1))
    kb.button(text='❎ Отказываюсь', callback_data=Tutorial(action='discontinue_1', lvl=1))
    kb.button(text='➕ Добавить бота в чат', url='http://t.me/epidemic2_bot?startgroup=iris&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users')
    
    kb.adjust(1)
    return kb.as_markup()

def help_kb():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='📖 Гайд по игре', url='https://teletype.in/@epidemic_gamebot/guide_epidemic')
    kb.button(text='➕ Добавить бота в чат', url='http://t.me/epidemic2_bot?startgroup=iris&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users')
    
    kb.adjust(1)
    return kb.as_markup()

def tutorial_continue():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Продолжить курс ❇️', callback_data=Tutorial(lvl=2))
    
    kb.adjust(1)
    return kb.as_markup()

def tutorial_2_kb():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Продолжить курс ❇️', callback_data=Tutorial(lvl=3))
    
    kb.adjust(1)
    return kb.as_markup()

def tutorial_3_kb():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Продолжить курс ❇️', callback_data=Tutorial(lvl=4))
    
    kb.adjust(1)
    return kb.as_markup()

def tutorial_4_kb():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Продолжить курс ❇️', callback_data=Tutorial(lvl=5))
    
    kb.adjust(1)
    return kb.as_markup()

def tutorial_5_kb():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Продолжить курс ❇️', callback_data=Tutorial(lvl=6))
    
    kb.adjust(1)
    return kb.as_markup()

def tutorial_6_kb():
    kb = InlineKeyboardBuilder()
    
    kb.button(text='Продолжить курс ❇️', callback_data=Tutorial(lvl=7))
    
    kb.adjust(1)
    return kb.as_markup()


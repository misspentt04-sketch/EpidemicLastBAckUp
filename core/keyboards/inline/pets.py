from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.utils.callbackdata import PetsListChoose, PetsGlobalListChoose
from core.data.tricks.tricks_biowar import tricks_biowar

def pets_list_nav(user_id: int, pets: dict):
    kb = InlineKeyboardBuilder()
    
    for i in pets:
        emoji = tricks_biowar['pet']['pets_info'][i['pet_name'].lower()]['emoji']
        kb.button(text=f'{emoji}', callback_data=PetsListChoose(pet=i['pet_name'], user_id=user_id))
    
    kb.adjust(5,5,5)
    return kb.as_markup(resize_keyboard=True)

def global_pets_list_nav(user_id: int):
    kb = InlineKeyboardBuilder()
    
    pets = tricks_biowar['pet']['pets_info']
    
    for key, val in pets.items():
        emoji = val['emoji']
        kb.button(text=f'{emoji}', callback_data=PetsGlobalListChoose(pet=key, user_id=user_id))
    
    kb.adjust(5,5,5)
    return kb.as_markup(resize_keyboard=True)
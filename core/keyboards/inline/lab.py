from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.utils.callbackdata import Lab, LabLvlUpConfirm, LabLvlUpConfirmExtend
from core.data.icons import LabIco
from core.data.tricks.tricks_biowar import tricks_biowar

def lab_navigation(id: int, is_my_lab: bool):
    kb = InlineKeyboardBuilder()
    
    kb.button(text=LabIco.pathogens.value, callback_data=Lab(skill = 'lab_pathogens', lvl_up = 1, id=id, is_my_lab=is_my_lab))
    kb.button(text=LabIco.science.value, callback_data=Lab(skill = 'lab_science', lvl_up = 1, id=id, is_my_lab=is_my_lab))
    kb.button(text=LabIco.infect.value, callback_data=Lab(skill = 'lab_infect', lvl_up = 1, id=id, is_my_lab=is_my_lab))
    kb.button(text=LabIco.immunity.value, callback_data=Lab(skill = 'lab_immunity', lvl_up = 1, id=id, is_my_lab=is_my_lab))
    kb.button(text=LabIco.lethality.value, callback_data=Lab(skill = 'lab_lethality', lvl_up = 1, id=id, is_my_lab=is_my_lab))
    kb.button(text=LabIco.security_service.value, callback_data=Lab(skill = 'lab_security_service', lvl_up = 1, id=id, is_my_lab=is_my_lab))
    
    kb.adjust(3),
    return kb.as_markup(resize_keyboard=True)

def lab_confirm_upgrade(skill: str, lvl_up: int, id: int):
    kb = InlineKeyboardBuilder()
    
    skill = f'lab_confirm_{skill}'
    
    kb.button(text=tricks_biowar['text']['confirm_upgrade'], callback_data=LabLvlUpConfirm(skill = skill, lvl_up=lvl_up, id=id))
    
    return kb.as_markup(resize_keyboard=True)

def lab_confirm_upgrade_extend(skill: str, user_id: int):
    kb = InlineKeyboardBuilder()
    
    kb.button(text=f'1x {LabIco[skill].value}', callback_data=LabLvlUpConfirmExtend(skill = skill, lvl_up=1, user_id=user_id))
    kb.button(text=f'3x {LabIco[skill].value}', callback_data=LabLvlUpConfirmExtend(skill = skill, lvl_up=3, user_id=user_id))
    kb.button(text=f'5x {LabIco[skill].value}', callback_data=LabLvlUpConfirmExtend(skill = skill, lvl_up=5, user_id=user_id))

    return kb.as_markup()



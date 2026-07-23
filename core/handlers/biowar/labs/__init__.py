from aiogram import Router, F
from core.data import texttriggers as trg
from aiogram.filters import Command
from aiogram.enums import ChatType

from .lab import get_lab, lab_lvlup_skills
from .lab_inline import lab_lvlup, lab_lvlup_confirm, lab_lvl_up_confirm_extend
from .lab_addons import pathogen_name_change, lab_dossier, customization_emoji, change_lab_name
from .lab_biotop import biotop, biotop_chat

from core.utils.callbackdata import Lab, LabLvlUpConfirm, LabLvlUpConfirmExtend

lab_router = Router()

# Laboratory
lab_router.message.register(get_lab, F.text.regexp(trg.re_lab, mode='fullmatch'))
lab_router.message.register(lab_lvlup_skills, F.text.regexp(trg.re_lab_lvlup_skills, mode='fullmatch'))
lab_router.message.register(biotop, F.text.regexp(trg.re_lab_biotop, mode='fullmatch'))
lab_router.message.register(biotop_chat, F.text.regexp(trg.re_lab_biotop_chat, mode='fullmatch'))

# Lab Addons
lab_router.message.register(pathogen_name_change, F.text.regexp(trg.re_pathogen_name_change, mode='fullmatch') | F.text.regexp(trg.re_remove_pathogen_name, mode='fullmatch'))
lab_router.message.register(change_lab_name, F.text.regexp(trg.re_change_lab_name, mode='fullmatch') | F.text.regexp(trg.re_remove_lab_name, mode='fullmatch'))
lab_router.message.register(lab_dossier, F.text.regexp(trg.re_lab_dossier, mode='fullmatch'))
lab_router.message.register(customization_emoji, F.text.regexp(trg.re_customization_emoji, mode='fullmatch') | F.text.regexp(trg.re_remove_customization_emoji, mode='fullmatch'))

# Lab Inlines
lab_router.callback_query.register(lab_lvlup_confirm, LabLvlUpConfirm.filter(F.skill.startswith('lab_confirm_')))
lab_router.callback_query.register(lab_lvlup, Lab.filter(F.skill.startswith('lab_')))
lab_router.callback_query.register(lab_lvl_up_confirm_extend, LabLvlUpConfirmExtend.filter(F.action == 'lvlup_extend'))

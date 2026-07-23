from aiogram import Router, F
from core.data import texttriggers as trg
from core.utils.callbackdata import PetsListChoose
from core.filters.is_reply_to_pet_msg import IsReplyPetNotifyMsgFilter

from aiogram.filters import Command
from aiogram.enums import ChatType
from .pets import my_pet, my_pets, my_pets_choose
from .pets_addons import pet_the_pet, pet_notify_reply_answ

pets_router = Router()
pets_router2 = Router()

pets_router.message.register(my_pet, F.text.regexp(trg.re_my_pet, mode='fullmatch'))
pets_router.message.register(my_pets, F.text.regexp(trg.re_my_pets, mode='fullmatch'))
pets_router2.message.register(pet_the_pet, F.text.regexp(trg.pet_the_pet, mode='fullmatch') & F.reply_to_message & F.reply_to_message.sticker)
pets_router.callback_query.register(my_pets_choose, PetsListChoose.filter(F.action == 'pet_choose'))
pets_router2.message.register(pet_notify_reply_answ, IsReplyPetNotifyMsgFilter())

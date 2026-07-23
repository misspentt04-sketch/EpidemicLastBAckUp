from aiogram import Router, F
from core.data import texttriggers as trg
from aiogram.filters import Command
from aiogram.enums import ChatType
from .infect import infect
from .infect_addons import (
    buy_vaccine, victims_list, illnesses_list, add_virus_signal,
    del_virus_signal, buy_vaccine_joke
)

infect_router = Router()
infect2_router = Router()

infect2_router.message.register(
    infect,
    F.text.regexp(trg.re_infect, mode='fullmatch') | (F.text.regexp(trg.re_infect_reply, mode='fullmatch')) & F.reply_to_message
)

# Infect Addons
infect_router.message.register(buy_vaccine, F.text.regexp(trg.re_buy_vaccine, mode='fullmatch'))
infect_router.message.register(victims_list, F.text.regexp(trg.re_victims_list, mode='fullmatch'))
infect_router.message.register(illnesses_list, F.text.regexp(trg.re_illnesses_list, mode='fullmatch'))
infect_router.message.register(add_virus_signal, F.text.regexp(trg.re_add_virus_signal, mode='fullmatch'))
infect_router.message.register(del_virus_signal, F.text.regexp(trg.re_del_virus_signal, mode='fullmatch'))
infect_router.message.register(buy_vaccine_joke, F.text.regexp(trg.re_buy_vaccine_joke, mode='fullmatch'))
from .mf import cmd_mass_fallen, process_mf_page, process_mf_start
from aiogram import Router, F
from core.data import texttriggers as trg
from aiogram.filters import Command
from aiogram.enums import ChatType
from .infect import infect, cmd_check_victim, hit_target_callback
from .infect_addons import (
    buy_vaccine, victims_list, illnesses_list, add_virus_signal,
    del_virus_signal, buy_vaccine_joke
)

infect_router = Router()
infect2_router = Router()

# Заражение
infect_router.message.register(
    infect,
    F.text.regexp(trg.re_infect, mode='fullmatch') | (F.text.regexp(trg.re_infect_reply, mode='fullmatch') & F.reply_to_message)
)

# Infect Addons
infect_router.message.register(buy_vaccine, F.text.regexp(trg.re_buy_vaccine, mode='fullmatch'))
infect_router.message.register(buy_vaccine, F.text.lower() == "кв")

infect_router.message.register(victims_list, F.text.regexp(trg.re_victims_list, mode='fullmatch'))
infect_router.message.register(illnesses_list, F.text.regexp(trg.re_illnesses_list, mode='fullmatch'))
infect_router.message.register(add_virus_signal, F.text.regexp(trg.re_add_virus_signal, mode='fullmatch'))
infect_router.message.register(del_virus_signal, F.text.regexp(trg.re_del_virus_signal, mode='fullmatch'))
infect_router.message.register(buy_vaccine_joke, F.text.regexp(trg.re_buy_vaccine_joke, mode='fullmatch'))

# Check Victim Command (исправленный фильтр без дублирования)
infect_router.message.register(
    cmd_check_victim,
    F.text.lower().split()[0].in_({'.ч', '!ч', '/ч', 'ч', '.чек', '!чек', '/чек', 'чек'})
)

infect_router.callback_query.register(hit_target_callback, F.data.startswith('hit_target:'))

# Mass Fallen
infect_router.message.register(cmd_mass_fallen, F.text.lower() == 'мф')
infect_router.callback_query.register(process_mf_page, F.data.startswith('mf_page:'))
infect_router.callback_query.register(process_mf_start, F.data.startswith('mf_start:'))

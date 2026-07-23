from aiogram import Router, F

from core.data import texttriggers as trg
from .event import (
    my_event_information, event_biotop, send_valentinka,
    send_gift, one_april_joke, aprelki
)

event_router = Router()


# event_router.message.register(my_event_information, F.text.regexp(trg.re_my_event_information, mode='fullmatch'))
# event_router.message.register(event_biotop, F.text.regexp(trg.re_event_biotop, mode='fullmatch'))
# event_router.message.register(send_valentinka, F.text.regexp(trg.re_send_valentinka, mode='fullmatch'))
# event_router.message.register(send_gift, F.text.regexp(trg.re_send_gift, mode='fullmatch'))
# event_router.message.register(one_april_joke, F.text.lower().regexp(r'(!|)-био(-|)войны', mode='fullmatch'))
# event_router.message.register(aprelki, F.text.lower().regexp(r'([!./]|)апрель(ка|к|)', mode='fullmatch'))


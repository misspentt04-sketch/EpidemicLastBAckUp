from aiogram import Router, F

from aiogram.filters.chat_member_updated import (
    ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
)
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, Command
from aiogram.enums import ChatType
from core.utils.callbackdata import (
    about_marriage_data, accept_marriage_data, reject_marriage_data, 
    accept_MarriageDevorce_data, reject_MarriageDevorce_data,
    reject_restore_marrige_data, accept_restore_marrige_data,
    close_marriage_data, top_marriages_data, top_exp_data, top_sms_data
    )

from core.data import texttriggers as trg
from core.filters.is_in_rplist import IsRPFilter

from .admin import (
    get_admin
)
from .ping import ping
from .get_ids import get_chat_id, get_user_id
from .notes import show_notes, add_note, del_note, show_note
from .rules import add_rules, get_rules, del_rules
from .chat_mem_notifications import include_hello_not, include_leave_not
from .help import help
from .rp_cmd import rp_handler
from .chat_nickname import set_nickname
from .bot_pm import bot_pm


addions_router = Router()

# Ping
addions_router.message.register(ping, F.text.regexp(trg.re_ping, mode='fullmatch'))

# Notes
addions_router.message.register(show_notes, F.text.regexp(trg.re_show_notes, mode='fullmatch') & (F.chat.type != 'private'))
addions_router.message.register(show_note, F.text.regexp(trg.re_show_note, mode='fullmatch') & (F.chat.type != 'private'))

addions_router.message.register(add_note, F.text.regexp(trg.re_add_note, mode='fullmatch') & (F.chat.type != 'private'))

addions_router.message.register(del_note, F.text.regexp(trg.re_del_note, mode='fullmatch') & (F.chat.type != 'private'))

# IDS
addions_router.message.register(get_user_id, F.text.regexp(trg.re_get_id, mode='fullmatch'))
addions_router.message.register(get_chat_id, F.text.regexp(trg.re_check_chat_id, mode='fullmatch'))

# Rules
addions_router.message.register(add_rules, F.text.regexp(trg.re_add_rules, mode='fullmatch') & (F.chat.type != 'private'))
addions_router.message.register(get_rules, F.text.regexp(trg.re_get_rules, mode='fullmatch') & (F.chat.type != 'private'))
addions_router.message.register(del_rules, F.text.regexp(trg.re_del_rules, mode='fullmatch') & (F.chat.type != 'private'))

# Admins
addions_router.message.register(get_admin, F.text.regexp(trg.re_get_admins, mode='fullmatch') & (F.chat.type != 'private'))

# Hello notifications
addions_router.message.register(include_hello_not, F.text.regexp(trg.re_edit_greeting_on, mode='fullmatch') & (F.chat.type != 'private'))

# Leave notifications
addions_router.message.register(include_leave_not, F.text.regexp(trg.re_edit_leave_on, mode='fullmatch') & (F.chat.type != 'private'))

# help
addions_router.message.register(help,  F.text.regexp(trg.re_help, mode='fullmatch'))

# Rp
addions_router.message.register(rp_handler, IsRPFilter())

# User chat nickname
addions_router.message.register(set_nickname, F.text.regexp(trg.set_nickname, mode='fullmatch'))

# Bot pm
addions_router.message.register(bot_pm, F.text.regexp(trg.re_bot_pm, mode='fullmatch'))
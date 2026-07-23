from aiogram import Router, F
from core.utils.callbackdata import Corporation
from core.data import texttriggers as trg
from aiogram.filters import Command
from aiogram.enums import ChatType
from .corporations_inline import corporation_get_members, invite_request_corporation_inline
from .corporations import (
    get_corporation, create_corporation, delete_corporation,
    invite_request_corporation, invite_accept_corporation, invite_reject_corporation,
    get_corporation_members, leave_corporation, kick_from_corporation,
    get_corporation_invites, change_corporation_name, deladd_corporation_admin,
    get_corporation_admins, corporation_dossier, get_corporations_biotop
)

corporation_router = Router()

corporation_router.message.register(get_corporation, F.text.regexp(trg.re_get_corporation, mode='fullmatch'))
corporation_router.message.register(create_corporation, F.text.regexp(trg.re_create_corporation, mode='fullmatch'))
corporation_router.message.register(delete_corporation, F.text.regexp(trg.re_delete_corporation, mode='fullmatch'))
corporation_router.message.register(invite_request_corporation, F.text.regexp(trg.re_invite_request_corporation, mode='fullmatch'))
corporation_router.message.register(invite_accept_corporation, F.text.regexp(trg.re_invite_accept_corporation, mode='fullmatch'))
corporation_router.message.register(invite_reject_corporation, F.text.regexp(trg.re_invite_reject_corporation, mode='fullmatch'))
corporation_router.message.register(get_corporation_members, F.text.regexp(trg.re_get_corporation_members, mode='fullmatch'))
corporation_router.message.register(get_corporation_invites, F.text.regexp(trg.re_get_corp_invites, mode='fullmatch'))
corporation_router.message.register(leave_corporation, F.text.regexp(trg.leave_corporation, mode='fullmatch'))
corporation_router.message.register(kick_from_corporation, F.text.regexp(trg.re_kick_from_corporation, mode='fullmatch'))
corporation_router.message.register(change_corporation_name, F.text.regexp(trg.re_change_corporation_name, mode='fullmatch'))
corporation_router.message.register(deladd_corporation_admin, F.text.regexp(trg.re_deladd_corporation_admin, mode='fullmatch'))
corporation_router.message.register(get_corporation_admins, F.text.regexp(trg.re_get_corporation_admins, mode='fullmatch'))
corporation_router.message.register(corporation_dossier, F.text.regexp(trg.re_corporation_dossier, mode='fullmatch'))
corporation_router.message.register(get_corporations_biotop, F.text.regexp(trg.re_corporations_biotop, mode='fullmatch'))

# Corporation inline
corporation_router.callback_query.register(corporation_get_members, Corporation.filter(F.action == 'corp_get_members'))
corporation_router.callback_query.register(invite_request_corporation_inline, Corporation.filter(F.action == 'invite_request_corporation'))
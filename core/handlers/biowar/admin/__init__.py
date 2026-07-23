from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import Command, ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from core.filters import IsAdminFilter
from core.data import texttriggers as trg
from .chat_bot_update import (
    bot_added_to_group,
    new_chat_member, leave_chat_member, upd_chat_name
)
from .admin import (
    search_pathogen, all_game_bio_experience, pathogen_mute,
    game_mute, lab_transfer, game_mute_cancel, pathogen_mute_cancel, le,
    stop_bot, biomute_list, gamemute_list, check_the_mute, bot_statistics
)
from .user import (
    disable_biowar_chat, disalbe_biowar_user, enable_chat_biowar
)

admin_router = Router()
admin_router_global = Router()

IS_GROUP = F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])

# Admins commands
admin_router.message.register(search_pathogen, Command("search_pathogen"), IsAdminFilter())
admin_router.message.register(all_game_bio_experience, Command("game_exp"), IsAdminFilter())
admin_router.message.register(pathogen_mute, F.text.regexp(trg.re_pathogen_mute, mode='fullmatch'), IsAdminFilter())
admin_router.message.register(pathogen_mute_cancel, F.text.regexp(trg.re_pathogen_mute_cancel, mode='fullmatch'), IsAdminFilter())
admin_router.message.register(game_mute, F.text.regexp(trg.re_game_mute, mode='fullmatch'), IsAdminFilter())
admin_router.message.register(game_mute_cancel, F.text.regexp(trg.re_game_mute_cancel, mode='fullmatch'), IsAdminFilter())
admin_router.message.register(lab_transfer, F.text.regexp(trg.re_lab_transfer, mode='fullmatch'), IsAdminFilter())
admin_router.message.register(stop_bot, F.text == '!epidemic_stop', IsAdminFilter())
admin_router.message.register(biomute_list, F.text.lower() == '!эпимут', IsAdminFilter())
admin_router.message.register(gamemute_list, F.text.lower() == '!эпиас', IsAdminFilter())
admin_router.message.register(check_the_mute, F.text.regexp(trg.re_check_gamemute, mode='fullmatch'), IsAdminFilter())
admin_router.message.register(bot_statistics, F.text.lower() == '!стата', IsAdminFilter())

# Chat Bot Update
admin_router.chat_member.register(new_chat_member, ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION), IS_GROUP)
admin_router.chat_member.register(leave_chat_member, ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION), IS_GROUP)
admin_router.my_chat_member.register(bot_added_to_group, ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION), IS_GROUP)
#admin_router.message.register(group_to_supegroup_migration, F.migrate_to_chat_id & F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
admin_router.message.register(upd_chat_name, F.new_chat_title)

# User
admin_router_global.message.register(disable_biowar_chat, F.text.lower() == '!-чат биовойны')
admin_router_global.message.register(disalbe_biowar_user, F.text.lower() == '!-биовойны')
admin_router_global.message.register(enable_chat_biowar, F.text.lower() == '!+чат биовойны')

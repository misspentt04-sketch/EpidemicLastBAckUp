from aiogram.filters import Command
from aiogram import Router, F

from core.data import texttriggers as trg

from core.utils.callbackdata import Tutorial

### Story ###

from .tutorial_begin import (
    tutorial_1_continue, tutorial_1_discontinue, restart_tutorial,
    tutorial_2, tutorial_3, tutorial_4, tutorial_5,
    tutorial_6, tutorial_7
)

tutorial_router = Router()


# # Story start action
# router.message.register(lab_dossier, F.text.regexp(trg.re_lab_dossier, mode='fullmatch'))

# Story start action inline
# tutorial_router.callback_query.register(tutorial_start_action, TutorialStartAction.filter(F.action == 'tutorial_start_action'))
tutorial_router.callback_query.register(tutorial_1_continue, Tutorial.filter(F.action == 'continue_1'))
tutorial_router.callback_query.register(tutorial_1_discontinue, Tutorial.filter(F.action == 'discontinue_1'))
tutorial_router.message.register(restart_tutorial, Command('restart_tutorial'), F.chat.type == 'private')

tutorial_router.callback_query.register(tutorial_2, Tutorial.filter(F.lvl == 2))
tutorial_router.callback_query.register(tutorial_3, Tutorial.filter(F.lvl == 3))
tutorial_router.callback_query.register(tutorial_4, Tutorial.filter(F.lvl == 4))
tutorial_router.callback_query.register(tutorial_5, Tutorial.filter(F.lvl == 5))
tutorial_router.callback_query.register(tutorial_6, Tutorial.filter(F.lvl == 6))
tutorial_router.callback_query.register(tutorial_7, Tutorial.filter(F.lvl == 7))


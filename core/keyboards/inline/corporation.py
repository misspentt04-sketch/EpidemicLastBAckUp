from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.utils.callbackdata import Corporation
from core.data.icons import LabIco  # noqa: F401


def corp_navigation(id: int, corp_code: str, dossier_open: bool = True,
                    is_member: bool = True, can_dossier: bool = False):
    kb = InlineKeyboardBuilder()

    kb.button(
        text='👥 Участники',
        callback_data=Corporation(id=id, action='corp_get_members', corp_code=corp_code),
    )
    kb.button(
        text='📋 Заявки',
        callback_data=Corporation(id=id, action='corp_get_invites', corp_code=corp_code),
    )

    if is_member:
        # Досье — только для владельца/соруков
        if can_dossier:
            kb.button(
                text=f"📖 Досье: {'🔓' if dossier_open else '🔒'}",
                callback_data=Corporation(id=id, action='corp_toggle_dossier', corp_code=corp_code),
            )
        kb.button(
            text='💰 Казна',
            callback_data=Corporation(id=id, action='corp_treasury_menu', corp_code=corp_code),
        )
        kb.button(
            text='⭐ Прокачать корпу',
            callback_data=Corporation(id=id, action='corp_upgrade_menu', corp_code=corp_code),
        )
        # Пересчитаем adjust: 2 сверху, потом строка с досье+казна, потом прокачка
        if can_dossier:
            kb.adjust(2, 2, 1)
        else:
            kb.adjust(2, 1, 1)
    else:
        kb.button(
            text='✉️ Вступить',
            callback_data=Corporation(id=id, action='invite_request_corporation', corp_code=corp_code),
        )
        kb.adjust(2, 1)

    return kb.as_markup()


def corp_upgrade_menu_kb(id: int, corp_code: str, can_upgrade: bool = True):
    kb = InlineKeyboardBuilder()
    if can_upgrade:
        kb.button(
            text='⭐ Прокачать',
            callback_data=Corporation(id=id, action='corp_upgrade_confirm', corp_code=corp_code),
        )
    kb.button(
        text='⬅️ Назад',
        callback_data=Corporation(id=id, action='corp_back_to_main', corp_code=corp_code),
    )
    kb.adjust(1)
    return kb.as_markup()


def corp_treasury_menu_kb(id: int, corp_code: str):
    kb = InlineKeyboardBuilder()
    kb.button(
        text='⬅️ Назад',
        callback_data=Corporation(id=id, action='corp_back_to_main', corp_code=corp_code),
    )
    kb.adjust(1)
    return kb.as_markup()

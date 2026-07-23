from aiogram.utils.keyboard import InlineKeyboardBuilder


def suggestions_menu():
    kb = InlineKeyboardBuilder()

    kb.button(text="🐞 Баг", callback_data="suggest_bug")
    kb.button(text="💡 Идея", callback_data="suggest_idea")
    kb.button(text="➕ Команда", callback_data="suggest_command")
    kb.button(text="🎮 Разнообразие", callback_data="suggest_game")

    kb.adjust(2)

    return kb.as_markup()
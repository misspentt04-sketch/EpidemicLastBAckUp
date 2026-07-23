from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

ADMIN_CHAT = -1004453274975


class SuggestionState(StatesGroup):
    waiting_text = State()


CATEGORIES = {
    "idea_bug": "рџђћ Р‘Р°Рі",
    "idea_game": "рџ’Ў РРґРµСЏ",
    "idea_command": "вћ• РљРѕРјР°РЅРґР°",
    "idea_fun": "рџЋ® Р Р°Р·РЅРѕРѕР±СЂР°Р·РёРµ",
}


@router.message(F.text == "рџ’Ў РџСЂРµРґР»РѕР¶РµРЅРёСЏ")
async def suggestions_menu(message: Message):
    kb = InlineKeyboardBuilder()

    kb.button(text="рџђћ Р‘Р°Рі", callback_data="idea_bug")
    kb.button(text="рџ’Ў РРґРµСЏ", callback_data="idea_game")
    kb.button(text="вћ• РљРѕРјР°РЅРґР°", callback_data="idea_command")
    kb.button(text="рџЋ® Р Р°Р·РЅРѕРѕР±СЂР°Р·РёРµ", callback_data="idea_fun")

    kb.adjust(2)

    await message.answer(
        "Р’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РїСЂРµРґР»РѕР¶РµРЅРёСЏ:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.in_(CATEGORIES.keys()))
async def suggestion_category(callback: CallbackQuery, state: FSMContext):
    await state.update_data(category=callback.data)

    await callback.message.edit_text(
        f"РљР°С‚РµРіРѕСЂРёСЏ: {CATEGORIES[callback.data]}\n\n"
        "РўРµРїРµСЂСЊ РѕС‚РїСЂР°РІСЊС‚Рµ РІР°С€Рµ РїСЂРµРґР»РѕР¶РµРЅРёРµ РѕРґРЅРёРј СЃРѕРѕР±С‰РµРЅРёРµРј."
    )

    await state.set_state(SuggestionState.waiting_text)
    await callback.answer()


@router.message(SuggestionState.waiting_text)
async def suggestion_send(message: Message, state: FSMContext):

    data = await state.get_data()
    category = CATEGORIES[data["category"]]

    text = (
        f"рџ“© <b>РќРѕРІРѕРµ РїСЂРµРґР»РѕР¶РµРЅРёРµ</b>\n\n"
        f"<b>РљР°С‚РµРіРѕСЂРёСЏ:</b> {category}\n"
        f"<b>РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ:</b> {message.from_user.full_name}\n"
        f"<b>ID:</b> <code>{message.from_user.id}</code>\n"
    )

    if message.from_user.username:
        text += f"<b>Username:</b> @{message.from_user.username}\n"

    text += f"\n<b>РўРµРєСЃС‚:</b>\n{message.text}"

    await message.bot.send_message(
        ADMIN_CHAT,
        text
    )

    await message.answer(
        "вњ… РЎРїР°СЃРёР±Рѕ! Р’Р°С€Рµ РїСЂРµРґР»РѕР¶РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ Р°РґРјРёРЅРёСЃС‚СЂР°С†РёРё."
    )

    await state.clear()

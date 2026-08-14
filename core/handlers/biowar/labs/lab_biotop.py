from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, F, Router
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar
from core import func
from humanize import intcomma

router = Router()

def get_biotop_keyboard(user_id: int, current_page: int = 1) -> InlineKeyboardMarkup:
    btn1_text = "• 1 •" if current_page == 1 else "1"
    btn2_text = "• 2 •" if current_page == 2 else "2"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn1_text, callback_data=f"biotop_page:1:{user_id}"),
                InlineKeyboardButton(text=btn2_text, callback_data=f"biotop_page:2:{user_id}"),
            ]
        ]
    )
    return keyboard

async def biotop(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    biotop_data = await repo_biowar.get_lab_biotop()
    biotop_list = func.get_biotop_lab(biotop_data, page=1)

    text = tricks_biowar['biotops']['lab'].format(
        '\n'.join(biotop_list[0]), intcomma(biotop_list[1][0])
    )

    reply_markup = get_biotop_keyboard(user_id=user_id, current_page=1)
    await msg.answer(text, reply_markup=reply_markup)


async def biotop_chat(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    biotop_data = await repo_biowar.get_lab_biotop_chat(msg.chat.id)
    chat_biotop_list = func.get_biotop_lab(biotop_data, page=1)

    text = tricks_biowar['biotops']['lab_chat'].format(
        '\n'.join(chat_biotop_list[0]), intcomma(chat_biotop_list[1][0])
    )

    reply_markup = get_biotop_keyboard(user_id=user_id, current_page=1)
    await msg.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("biotop_page:"))
async def biotop_page_callback(call: CallbackQuery, repo_biowar: RequestsRepoBiowar):
    _, page_str, target_user_id_str = call.data.split(":")
    page = int(page_str)
    target_user_id = int(target_user_id_str)

    if call.from_user.id != target_user_id:
        await call.answer("❌ Переключать страницы может только тот, кто вызвал команду!", show_alert=True)
        return

    biotop_data = await repo_biowar.get_lab_biotop()
    biotop_list = func.get_biotop_lab(biotop_data, page=page)

    text = tricks_biowar['biotops']['lab'].format(
        '\n'.join(biotop_list[0]), intcomma(biotop_list[1][0])
    )

    reply_markup = get_biotop_keyboard(user_id=target_user_id, current_page=page)
    
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        pass
    await call.answer()

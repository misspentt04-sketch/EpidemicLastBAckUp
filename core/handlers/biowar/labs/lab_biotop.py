from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, F, Router
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar
from core import func
from humanize import intcomma

router = Router()

def get_biotop_keyboard(user_id: int, current_page: int = 1, biotop_type: str = "lab") -> InlineKeyboardMarkup:
    btn1_text = "• 1 •" if current_page == 1 else "1"
    btn2_text = "• 2 •" if current_page == 2 else "2"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn1_text, callback_data=f"biotop_page:{biotop_type}:1:{user_id}"),
                InlineKeyboardButton(text=btn2_text, callback_data=f"biotop_page:{biotop_type}:2:{user_id}"),
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

    reply_markup = get_biotop_keyboard(user_id=user_id, current_page=1, biotop_type="lab")
    await msg.answer(text, reply_markup=reply_markup)


async def biotop_chat(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    biotop_data = await repo_biowar.get_lab_biotop_chat(chat_id)
    chat_biotop_list = func.get_biotop_lab(biotop_data, page=1)

    text = tricks_biowar['biotops']['lab_chat'].format(
        '\n'.join(chat_biotop_list[0]), intcomma(chat_biotop_list[1][0])
    )

    reply_markup = get_biotop_keyboard(user_id=user_id, current_page=1, biotop_type="chat")
    await msg.answer(text, reply_markup=reply_markup)


@router.callback_query(F.data.startswith("biotop_page:"))
async def biotop_page_callback(call: CallbackQuery, repo_biowar: RequestsRepoBiowar):
    parts = call.data.split(":")
    biotop_type = parts[1]
    page = int(parts[2])
    target_user_id = int(parts[3])

    if call.from_user.id != target_user_id:
        await call.answer("❌ Переключать страницы может только тот, кто вызвал команду!", show_alert=True)
        return

    if biotop_type == "chat":
        biotop_data = await repo_biowar.get_lab_biotop_chat(call.message.chat.id)
        text_template = tricks_biowar['biotops']['lab_chat']
    else:
        biotop_data = await repo_biowar.get_lab_biotop()
        text_template = tricks_biowar['biotops']['lab']

    biotop_list = func.get_biotop_lab(biotop_data, page=page)

    text = text_template.format(
        '\n'.join(biotop_list[0]), intcomma(biotop_list[1][0])
    )

    reply_markup = get_biotop_keyboard(user_id=target_user_id, current_page=page, biotop_type=biotop_type)

    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        pass
    await call.answer()

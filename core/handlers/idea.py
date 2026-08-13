import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from redis.asyncio import Redis

idea_router = Router()

ADMIN_ID = -1003688648228 
COOLDOWN_SECONDS = 300  # 5 минут

class IdeaStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()

def get_idea_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💡 Идея / Предложение", callback_data="idea_cat_idea"),
            InlineKeyboardButton(text="🐛 Сообщить о баге", callback_data="idea_cat_bug")
        ],
        [
            InlineKeyboardButton(text="🛑 Жалоба на игрока", callback_data="idea_cat_complaint"),
            InlineKeyboardButton(text="❓ Другой вопрос", callback_data="idea_cat_other")
        ]
    ])

@idea_router.message(F.text == "/idea")
async def cmd_idea(msg: Message, redis: Redis):
    user_id = msg.from_user.id
    
    if user_id != ADMIN_ID:
        cooldown_key = f"idea_cooldown:{user_id}"
        ttl = await redis.ttl(cooldown_key)
        if ttl > 0:
            minutes = ttl // 60
            seconds = ttl % 60
            return await msg.answer(f"⏳ Отправлять обращения можно раз в 5 минут.\nПодождите ещё {minutes} мин. {seconds} сек.")

    text = (
        "👋 <b>Центр поддержки и предложений</b>\n\n"
        "Выберите категорию обращения:"
    )
    await msg.answer(text, reply_markup=get_idea_keyboard())

@idea_router.callback_query(F.data.startswith("idea_cat_"))
async def process_idea_category(callback: CallbackQuery, state: FSMContext):
    categories = {
        "idea_cat_idea": "💡 Идея / Предложение",
        "idea_cat_bug": "🐛 Сообщить о баге",
        "idea_cat_complaint": "🛑 Жалоба на игрока",
        "idea_cat_other": "❓ Другой вопрос"
    }
    
    cat_name = categories.get(callback.data, "Обращение")
    await state.update_data(category=cat_name)
    await state.set_state(IdeaStates.waiting_for_message)
    
    await callback.message.edit_text(
        f"Вы выбрали: <b>{cat_name}</b>\n\n"
        "💬 Отправьте ваше сообщение следующим сообщением.\n"
        "<i>Вы можете прикрепить текст, фото или видео.</i>"
    )
    await callback.answer()

@idea_router.message(IdeaStates.waiting_for_message)
async def send_idea_to_admin(msg: Message, state: FSMContext, bot: Bot, redis: Redis):
    data = await state.get_data()
    category = data.get("category", "💡 Идея / Предложение")
    await state.clear()
    
    user = msg.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✉️ Ответить", callback_data=f"idea_reply_{user.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"idea_reject_{user.id}")
        ]
    ])
    
    info_header = (
        f"✉️ <b>Новое обращение в поддержку!</b>\n\n"
        f"<b>Категория:</b> {category}\n"
        f"<b>От кого:</b> {user.full_name} ({username})\n"
        f"<b>ID пользователя:</b> <code>{user.id}</code>\n\n"
    )
    
    if msg.text or msg.caption:
        user_text = msg.text or msg.caption
        full_text = info_header + f"<b>Сообщение:</b>\n{user_text}"
        sent_msg = await bot.send_message(ADMIN_ID, full_text, parse_mode="HTML", reply_markup=admin_kb)
        try:
            await bot.pin_chat_message(chat_id=ADMIN_ID, message_id=sent_msg.message_id)
        except Exception as e:
            print(f"Не удалось закрепить сообщение: {e}")
    else:
        await bot.send_message(ADMIN_ID, info_header, parse_mode="HTML")
        await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=msg.chat.id, message_id=msg.message_id, reply_markup=admin_kb)
    
    if user.id != ADMIN_ID:
        cooldown_key = f"idea_cooldown:{user.id}"
        await redis.set(cooldown_key, "1", ex=COOLDOWN_SECONDS)
    
    await msg.answer("✅ Ваше сообщение успешно отправлено администрации! Спасибо за обратную связь.")

@idea_router.callback_query(F.data.startswith("idea_reject_"))
async def process_idea_reject(callback: CallbackQuery, bot: Bot):
    target_user_id = int(callback.data.split("_")[2])
    
    try:
        await bot.send_message(
            target_user_id,
            "❌ Ваше обращение было рассмотрено администрацией, но к сожалению, отклонено."
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление пользователю: {e}")
        
    await callback.message.edit_text(
        callback.message.html_text + "\n\n❌ <b>Статус:</b> Отклонено",
        reply_markup=None
    )
    await callback.answer("Обращение отклонено.")

@idea_router.callback_query(F.data.startswith("idea_reply_"))
async def process_idea_reply_start(callback: CallbackQuery, state: FSMContext):
    target_user_id = int(callback.data.split("_")[2])
    await state.update_data(reply_to_user=target_user_id, admin_msg_id=callback.message.message_id)
    await state.set_state(IdeaStates.waiting_for_reply)
    
    await callback.message.answer("✍️ Отправьте ответное сообщение пользователю следующим сообщением:")
    await callback.answer()

@idea_router.message(IdeaStates.waiting_for_reply)
async def process_idea_reply_send(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_user_id = data.get("reply_to_user")
    await state.clear()
    
    try:
        await bot.send_message(
            target_user_id,
            f"📩 <b>Ответ от администрации:</b>\n\n{msg.text or msg.caption or ''}",
            parse_mode="HTML"
        )
        if not msg.text:
            await bot.copy_message(chat_id=target_user_id, from_chat_id=msg.chat.id, message_id=msg.message_id)
        await msg.answer("✅ Ответ успешно отправлен пользователю!")
    except Exception as e:
        await msg.answer(f"❌ Ошибка отправки сообщения пользователю: {e}")

from aiogram import F
from aiogram.types import Message

@idea_router.message(F.text.casefold() == "бот")
async def bot_ping_handler(msg: Message):

    import os
    if os.path.exists("/home/ubuntu/epidemic/maintenance.flag") and msg.from_user and msg.from_user.id not in {7972320837, 7958133684}:
        return
    start_time = time.perf_counter()
    ping_msg = await msg.answer("<b>Epidemic System</b>", parse_mode="HTML")
    latency = round((time.perf_counter() - start_time) * 1000)
    
    text = (
        "🧪 <b>Epidemic System</b>\n"
        "├ <b>Статус:</b> Онлайн 🟢\n"
        f"└ <b>Задержка:</b> {latency} ms ⚡️"
    ).replace("\\n", "\n")
    
    await ping_msg.edit_text(text, parse_mode="HTML")

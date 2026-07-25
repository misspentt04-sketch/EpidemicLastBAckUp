import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
logger = logging.getLogger(__name__)

OWNER_IDEA_ID = 7972320837

class IdeaStates(StatesGroup):
    waiting_for_idea = State()

# Если вызов идет через текстовую команду !idea или !идея
@router.message(F.text.regexp(r'^!(?:идея|idea)', flags=re.IGNORECASE))
async def cmd_idea_start(message: Message, state: FSMContext):
    await state.set_state(IdeaStates.waiting_for_idea)
    await message.answer(
        "💡 <b>Отправьте вашу идею одним сообщением.</b>\n"
        "Вы можете написать подробный текст и прикрепить к нему фотографию или видео."
    )

# Обработка того самого сообщения от пользователя в состоянии ожидания
@router.message(IdeaStates.waiting_for_idea, F.content_types.in_({'text', 'photo', 'video'}))
async def process_idea_content(message: Message, state: FSMContext):
    await state.clear()
    
    user = message.from_user
    user_info = f"👤 От: {user.full_name} (@{user.username}, <code>{user.id}</code>)"
    
    try:
        # Сначала отправляем инфо о пользователе владельцу
        await message.bot.send_message(
            OWNER_IDEA_ID,
            f"💡 <b>Новое предложение / идея:</b>\n{user_info}",
            parse_mode="HTML"
        )
        # Пересылаем само сообщение (текст / фото / видео)
        await message.forward(OWNER_IDEA_ID)
        
        # Отвечаем строго одним сообщением игроку
        await message.answer("✅ Ваше сообщение успешно отправлено администрации! Спасибо за обратную связь.")
    except Exception as e:
        logger.error(f"Failed to send idea: {e}")
        await message.answer("❌ Произошла ошибка при отправке. Попробуйте позже.")

@router.message(IdeaStates.waiting_for_idea)
async def process_idea_wrong_type(message: Message):
    await message.answer("⚠️ Пожалуйста, отправьте текстовое сообщение, фотографию или видео.")

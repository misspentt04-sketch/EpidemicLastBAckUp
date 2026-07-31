import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.filters.state import StateFilter
from aiogram.enums.chat_type import ChatType
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from redis.asyncio import Redis
from asyncmy.cursors import DictCursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.story.story import tricks_story
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.keyboards.inline.tutorial_begin import start_action, help_kb

logger = logging.getLogger(__name__)
start_router = Router()

LOG_CHAT_ID = -1003688648228
REFERRAL_BONUS = 150
MAX_REFERRALS = 50

@start_router.message(CommandStart(), StateFilter('*'))
async def start_cmd(
    msg: Message,
    command: CommandObject,
    db: DictCursor,
    bot: Bot,
    redis: Redis,
    repo_biowar: RequestsRepoBiowar,
    state: FSMContext
):
    if msg.chat.type != ChatType.PRIVATE:
        return

    await state.clear()

    user_id = msg.from_user.id
    full_name = msg.from_user.full_name
    username = msg.from_user.username
    args = command.args

    logger.info(f"🔥 [START_CMD] Вызов /start! User={user_id}, Args={args}")

    try:
        # Проверяем наличие записи в туториале напрямую через курсор БД
        await db.execute("SELECT * FROM tutorial WHERE user_id = %s", (user_id,))
        tutorial_data = await db.fetchone()
        is_new_user = tutorial_data is None

        logger.info(f"🔥 [START_CMD] Новый игрок (нет записи в tutorial)? -> {is_new_user}")

        # Регистрируем/обновляем юзера
        await repo_biowar.add_data_user(user_id, full_name, username)

        # Обработка реферальной системы
        if args and args.strip().startswith("ref"):
            ref_arg = args.strip()
            logger.info(f"🔥 [START_CMD] Передан реферальный аргумент: {ref_arg}")

            if is_new_user:
                try:
                    referrer_id = int(ref_arg.replace("ref", ""))
                    logger.info(f"🔥 [START_CMD] Referrer ID: {referrer_id}, New User ID: {user_id}")

                    if referrer_id != user_id:
                        ref_count = await repo_biowar.get_referral_count(referrer_id)
                        added = await repo_biowar.add_referral(referrer_id, user_id)

                        if added:
                            bonus_given = False
                            if ref_count < MAX_REFERRALS:
                                try:
                                    await repo_biowar.add_lab_epicoins(referrer_id, REFERRAL_BONUS)
                                    bonus_given = True
                                    logger.info(f"🔥 [START_CMD] Бонус +{REFERRAL_BONUS} начислен рефереру {referrer_id}")
                                except Exception as e:
                                    logger.error(f"❌ Ошибка начисления бонуса: {e}")

                            try:
                                bonus_text = f"🎁 Бонус: +{REFERRAL_BONUS} Эпи-коинов." if bonus_given else "⚠️ Бонус не начислен (лимит 50)."
                                await bot.send_message(
                                    LOG_CHAT_ID,
                                    f"👤 <b>Новый реферал!</b>\n"
                                    f"🆔 Пригласивший: <code>{referrer_id}</code>\n"
                                    f"🆕 Новый игрок: {full_name} (<code>{user_id}</code>)\n"
                                    f"{bonus_text}"
                                )
                            except Exception as e:
                                logger.error(f"❌ Ошибка отправки в лог-чат: {e}")

                            try:
                                msg_text = (
                                    f"🎉 По вашей ссылке зарегистрировался {full_name}!\n"
                                    f"🎁 Вам начислено <b>+{REFERRAL_BONUS}</b> Эпи-коинов." if bonus_given else
                                    f"🎉 По вашей ссылке зарегистрировался {full_name}!\nℹ️ Лимит наград за рефералов достигнут."
                                )
                                await bot.send_message(referrer_id, msg_text)
                            except Exception as e:
                                logger.error(f"❌ Ошибка отправки рефереру: {e}")

                except ValueError:
                    logger.warning(f"⚠️ Неверный формат реферального ID: {ref_arg}")

        # Создаем запись туториала если новый
        await repo_biowar.add_data_tutorial(user_id)
        
        # Перепроверяем актуальный статус туториала
        await db.execute("SELECT * FROM tutorial WHERE user_id = %s", (user_id,))
        tutorial = await db.fetchone()

        picture = await redis.get('epidemic_tutorial_begin_img')

        if tutorial and tutorial.get('is_tutorial_complete') == 0:
            if not picture:
                with open('media/tutorial_begin.jpg', 'rb') as img:
                    result = await msg.answer_photo(
                        BufferedInputFile(img.read(), filename='tutorial_begin.jpg'),
                        caption=tricks_story['start_action'],
                        reply_markup=start_action(),
                        disable_web_page_preview=True
                    )
                    await redis.set('epidemic_tutorial_begin_img', result.photo[-1].file_id)
            else:
                await msg.answer_photo(
                    picture,
                    caption=tricks_story['start_action'],
                    reply_markup=start_action(),
                    disable_web_page_preview=True
                )
        else:
            admin_list = tricks_cm['start']['menu_admin_list']
            online = [val for key, val in admin_list.items() if await redis.get(f'epidemic_help_admin_status:{key}')]
            offline = [val for key, val in admin_list.items() if not await redis.get(f'epidemic_help_admin_status:{key}')]

            text = tricks_cm['start']['menu'].format('\n'.join(online), '\n'.join(offline))
            await msg.answer(text, reply_markup=help_kb(), disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"❌ Ошибка в start_cmd: {e}", exc_info=True)

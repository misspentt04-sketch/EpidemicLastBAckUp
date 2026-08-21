import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram import types
from aiogram.filters import CommandStart, CommandObject
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()
logger = logging.getLogger(__name__)

LOG_CHAT_ID = -1003688648228
REFERRAL_BONUS = 150

@router.message(CommandStart())
async def check_chk(message: types.Message, command: CommandObject):
    if command.args and command.args.startswith("chk_"):
        return
async def cmd_start_ref(message: Message, command: CommandObject, repo_biowar: RequestsRepoBiowar, bot: Bot):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    args = command.args

    # Регистрируем / обновляем пользователя в базе
    await repo_biowar.add_data_user(user_id, full_name, username)

    # Обработка реферального аргумента
    if args:
        ref_arg = args.strip()
        if ref_arg.startswith("ref"):
            try:
                referrer_id = int(ref_arg.replace("ref", ""))
                if referrer_id != user_id:
                    try:
                        # Записываем реферала
                        added = await repo_biowar.add_referral(referrer_id, user_id)
                        if added:
                            # Начисляем Эпи-коины пригласившему
                            try:
                                await repo_biowar.add_lab_epicoins(referrer_id, REFERRAL_BONUS)
                            except Exception as bonus_err:
                                logger.error(f"Failed to add epicoins to {referrer_id}: {bonus_err}")

                            # Лог в чат логов
                            try:
                                await bot.send_message(
                                    LOG_CHAT_ID,
                                    f"👤 <b>Новый реферал!</b>\n"
                                    f"🆔 Пригласивший: <code>{referrer_id}</code>\n"
                                    f"🆕 Новый игрок: {full_name} (<code>{user_id}</code>)\n"
                                    f"🎁 Бонус: +{REFERRAL_BONUS} Эпи-коинов."
                                )
                            except Exception:
                                pass

                            # Уведомление пригласившему в ЛС
                            try:
                                await bot.send_message(
                                    referrer_id,
                                    f"🎉 По вашей ссылке зарегистрировался новый игрок {full_name}!\n"
                                    f"🎁 Вам начислено <b>+{REFERRAL_BONUS}</b> Эпи-коинов."
                                )
                            except Exception:
                                pass

                    except Exception as e:
                        logger.error(f"Failed to process referral for referrer_id={referrer_id}, user_id={user_id}: {e}")
            except ValueError:
                pass

    # Приветственное сообщение для игрока
    await message.answer(
        f"Добро пожаловать в <b>Epidemic</b>, {full_name}!\n\n"
        f"Вы успешно зарегистрировались в игре. Введите /help или используйте меню для начала игры."
    )

@router.message(F.text.in_({"рефералы", "/ref", "Рефералы"}))
async def cmd_referrals(message: Message, repo_biowar: RequestsRepoBiowar = None):
    if repo_biowar is None:
        await message.answer("Ошибка доступа к базе данных. Попробуйте позже.")
        return

    ref_count = await repo_biowar.get_referral_count(message.from_user.id)
    bot_user = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_user.username}?start=ref{message.from_user.id}"

    r5 = "✅" if ref_count >= 5 else f"({ref_count}/5)"
    r10 = "✅" if ref_count >= 10 else f"({ref_count}/10)"
    r15 = "✅" if ref_count >= 15 else f"({ref_count}/15)"
    r30 = "✅" if ref_count >= 30 else f"({ref_count}/30)"
    r35 = "✅" if ref_count >= 35 else f"({ref_count}/35)"
    r40 = "✅" if ref_count >= 40 else f"({ref_count}/40)"
    r50 = "✅" if ref_count >= 50 else f"({ref_count}/50)"

    text = (
        f"🔗 <b>Реферальная система</b>\n\n"
        f"Приглашайте друзей в игру и получайте награды! За каждого нового игрока вы получаете <b>{REFERRAL_BONUS} Эпи-коинов</b>.\n\n"
        f"👥 Приглашено новых игроков: <b>{ref_count}</b>\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{ref_link}</code>\n\n"
        f"🎁 <b>Прогресс наград:</b>\n"
        f"• 5 рефералов: 1 обычный кейс {r5}\n"
        f"• 10 рефералов: 1 обычный кейс {r10}\n"
        f"• 15 рефералов: 2 обычных кейса {r15}\n"
        f"• 30 рефералов: 1 донатный кейс (кейс 2) {r30}\n"
        f"• 35 рефералов: 1 обычный кейс {r35}\n"
        f"• 40 рефералов: 1 обычный кейс {r40}\n"
        f"• 50 рефералов: 1 донатный кейс (кейс 2) {r50}\n"
    )

    await message.answer(text)

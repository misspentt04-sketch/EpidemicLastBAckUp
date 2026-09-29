import logging
import time
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram import types
from aiogram.filters import CommandStart, CommandObject
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.referral_links import (
    get_or_create_referral_link,
    resolve_referral_code,
)

router = Router()
logger = logging.getLogger(__name__)

LOG_CHAT_ID = -1003688648228
REFERRAL_BONUS = 150


async def _get_pool():
    from core.utils.db_api.settings_pool import db_pool
    return await db_pool.get_pool()


@router.message(CommandStart())
async def check_chk(message: types.Message, command: CommandObject):
    if command.args and command.args.startswith("chk_"):
        return
    if command.args and command.args.startswith("ref"):
        return await cmd_start_ref(message, command)

    # Обычное /start
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            repo = RequestsRepoBiowar(cur)
            try:
                await repo.add_data_user(
                    message.from_user.id,
                    message.from_user.full_name,
                    message.from_user.username,
                )
            except Exception as e:
                logger.error(f"[START] add_data_user error: {e}")

    await message.answer(
        f"Добро пожаловать в <b>Epidemic</b>, {message.from_user.full_name}!\n\n"
        f"Введите /help или используйте меню для начала игры."
    )


async def cmd_start_ref(message: Message, command: CommandObject):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    args = command.args or ""

    # Разбор аргумента
    referrer_id = None
    ref_arg = args.strip()
    if ref_arg.startswith("ref"):
        code_or_id = ref_arg[3:].strip()

        if code_or_id.isdigit():
            candidate = int(code_or_id)
            if candidate != user_id:
                referrer_id = candidate
        elif code_or_id:
            try:
                pool = await _get_pool()
                referrer_id = await resolve_referral_code(pool, code_or_id)
                if referrer_id == user_id:
                    referrer_id = None
            except Exception as e:
                logger.error(f"[REF] resolve code error: {e}")
                referrer_id = None

    # Регистрация + реферал — в одном контексте
    pool = await _get_pool()
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                repo = RequestsRepoBiowar(cur)

                try:
                    await repo.add_data_user(user_id, full_name, username)
                except Exception as e:
                    logger.error(f"[START_REF] add_data_user error: {e}")

                if referrer_id is not None:
                    try:
                        added = await repo.add_referral(referrer_id, user_id)
                        if added:
                            try:
                                await repo.add_lab_epicoins(referrer_id, REFERRAL_BONUS)
                            except Exception as e:
                                logger.error(f"[REF] add_lab_epicoins error: {e}")

                            try:
                                await message.bot.send_message(
                                    LOG_CHAT_ID,
                                    f"👤 <b>Новый реферал!</b>\n"
                                    f"🆔 Пригласивший: <code>{referrer_id}</code>\n"
                                    f"🆕 Новый игрок: {full_name} (<code>{user_id}</code>)\n"
                                    f"🎁 Бонус: +{REFERRAL_BONUS} Эпи-коинов.",
                                )
                            except Exception:
                                pass

                            try:
                                await message.bot.send_message(
                                    referrer_id,
                                    f"🎉 По вашей ссылке зарегистрировался новый игрок {full_name}!\n"
                                    f"🎁 Вам начислено <b>+{REFERRAL_BONUS}</b> Эпи-коинов.",
                                )
                            except Exception:
                                pass
                    except Exception as e:
                        logger.error(f"[REF] process referral error: {e}")
    except Exception as e:
        logger.error(f"[START_REF] pool error: {e}")
        return await message.answer("Ошибка подключения к БД. Попробуйте позже.")

    await message.answer(
        f"Добро пожаловать в <b>Epidemic</b>, {full_name}!\n\n"
        f"Введите /help или используйте меню для начала игры."
    )


@router.message(F.text.in_({"рефералы", "/ref", "Рефералы"}))
async def cmd_referrals(message: Message):
    user_id = message.from_user.id

    # Ссылка
    try:
        pool = await _get_pool()
        code, expires_at = await get_or_create_referral_link(pool, user_id)
    except Exception as e:
        logger.error(f"[REF] get_or_create error: {e}")
        return await message.answer("❌ Не удалось создать реферальную ссылку.")

    bot_user = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_user.username}?start=ref{code}"

    left = max(0, expires_at - int(time.time()))
    h = left // 3600
    m = (left % 3600) // 60
    s = left % 60
    timer_str = f"{h}ч {m}м {s}с"

    # Счёт + список
    ref_count = 0
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) AS cnt FROM Referrals WHERE referrer_id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                if row:
                    ref_count = int(row["cnt"] if isinstance(row, dict) else row[0]) or 0

    except Exception as e:
        logger.error(f"[REF] count error: {e}")


    r5 = "✅" if ref_count >= 5 else f"({ref_count}/5)"
    r10 = "✅" if ref_count >= 10 else f"({ref_count}/10)"
    r15 = "✅" if ref_count >= 15 else f"({ref_count}/15)"
    r30 = "✅" if ref_count >= 30 else f"({ref_count}/30)"
    r35 = "✅" if ref_count >= 35 else f"({ref_count}/35)"
    r40 = "✅" if ref_count >= 40 else f"({ref_count}/40)"
    r50 = "✅" if ref_count >= 50 else f"({ref_count}/50)"

    text = (
        f"🔗 <b>Реферальная система</b>\n\n"
        f"Приглашайте друзей в игру и получайте награды! "
        f"За каждого нового игрока вы получаете <b>{REFERRAL_BONUS} Эпи-коинов</b>.\n\n"
        f"👥 Приглашено новых игроков: <b>{ref_count}</b>\n"
        f"🔗 Ваша реферальная ссылка (действует ещё <b>{timer_str}</b>):\n"
        f"<code>{ref_link}</code>\n\n"
        f"🎁 <b>Прогресс наград:</b>\n"
        f"• 5 рефералов: 1 обычный кейс {r5}\n"
        f"• 10 рефералов: 1 обычный кейс {r10}\n"
        f"• 15 рефералов: 2 обычных кейса {r15}\n"
        f"• 30 рефералов: 1 донатный кейс (кейс 2) {r30}\n"
        f"• 35 рефералов: 1 обычный кейс {r35}\n"
        f"• 40 рефералов: 1 обычный кейс {r40}\n"
        f"• 50 рефералов: 1 донатный кейс (кейс 2) {r50}\n"
    )

    await message.answer(text, disable_web_page_preview=True)

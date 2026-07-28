from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandStart, CommandObject
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()
LOG_CHAT_ID = -1003688648228
REFERRAL_BONUS = 150

@router.message(CommandStart())
async def cmd_start_ref(message: Message, command: CommandObject, repo: RequestsRepoBiowar, bot: Bot):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username
    args = command.args

    user_exists = await repo.check_user_exists_in_db(user_id)

    await repo.add_data_user(user_id, full_name, username)

    if not user_exists and args:
        ref_arg = args.strip()
        if ref_arg.startswith("ref"):
            try:
                referrer_id = int(ref_arg.replace("ref", ""))
                if referrer_id != user_id:
                    try:
                        await repo.add_referral(referrer_id, user_id)
                        await repo.add_lab_bio_currency(referrer_id, REFERRAL_BONUS)
                        await bot.send_message(
                            LOG_CHAT_ID,
                            f"👤 <b>Новый реферал!</b>\n"
                            f"🆔 Пригласивший: <code>{referrer_id}</code>\n"
                            f"🆕 Новый игрок: {full_name} (<code>{user_id}</code>)\n"
                            f"🎁 Бонус: +{REFERRAL_BONUS} био-ресурсов."
                        )
                    except Exception as e:
                        print(f"Failed to process referral: {e}")
            except ValueError:
                pass

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
        f"Приглашайте друзей в игру и получайте награды! За каждого нового игрока вы получаете <b>{REFERRAL_BONUS} коинов</b>.\n\n"
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

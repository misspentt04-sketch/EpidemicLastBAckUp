from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()
LOG_CHAT_ID = -1003688648228

@router.message(CommandStart())
async def cmd_start_ref(message: Message, repo: RequestsRepoBiowar):
    args = message.text.split(maxsplit=1)
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    user_exists = await repo.check_user_exists_in_db(user_id)
    await repo.add_data_user(user_id, full_name, username)

    if len(args) > 1 and args[1].startswith("ref"):
        try:
            referrer_id = int(args[1].replace("ref", ""))
            if not user_exists and referrer_id != user_id:
                added = await repo.add_referral(referrer_id, user_id)
                if added:
                    await repo.add_lab_bio_currency(referrer_id, 150)
                    try:
                        await message.bot.send_message(
                            LOG_CHAT_ID,
                            f"👤 <b>Новый реферал!</b>\n"
                            f"🆔 Пригласивший: <code>{referrer_id}</code>\n"
                            f"🆕 Новый игрок: {full_name} (<code>{user_id}</code>)\n"
                            f"🎁 Бонус: +150 био-ресурсов."
                        )
                    except Exception as e:
                        print(f"Failed to send ref log: {e}")
        except ValueError:
            pass

@router.message(F.text.in_({"рефералы", "/ref", "Рефералы"}))
async def cmd_referrals(message: Message, repo_biowar: RequestsRepoBiowar = None):
    if repo_biowar is None:
        await message.answer("Ошибка доступа к базе данных. Попробуйте позже.")
        return
    ref_count = await repo_biowar.get_referral_count(message.from_user.id)

    text = (
        f"🔗 <b>Реферальная система</b>\n\n"
        f"Приглашайте друзей в игру и получайте награды! За каждого нового игрока вы получаете <b>150 коинов</b>.\n\n"
        f"👥 Приглашено новых игроков: <b>{ref_count}</b>\n"
        f"🔗 Ваша реферальная ссылка:\n<code>{ref_link}</code>\n\n"
        f"🎁 <b>Прогресс наград:</b>\n"
        f"• 5 рефералов: 1 обычный кейс {"✅" if ref_count >= 5 else f"({ref_count}/5)"}\n"
        f"• 10 рефералов: 1 обычный кейс {"✅" if ref_count >= 10 else f"({ref_count}/10)"}\n"
        f"• 15 рефералов: 2 обычных кейса {"✅" if ref_count >= 15 else f"({ref_count}/15)"}\n"
        f"• 30 рефералов: 1 донатный кейс (кейс 2) {"✅" if ref_count >= 30 else f"({ref_count}/30)"}\n"
        f"• 35 рефералов: 1 донатный кейс (кейс 2) {"✅" if ref_count >= 35 else f"({ref_count}/35)"}\n"
        f"• 50 рефералов: 1 донатный кейс (кейс 2) {"✅" if ref_count >= 50 else f"({ref_count}/50)"}\n"
    )

    await message.answer(text)

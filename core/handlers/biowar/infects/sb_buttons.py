import logging
from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.cursors import DictCursor
from redis.asyncio import Redis
from asyncio import Lock

from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("sb_check:"))
async def cb_sb_check(callback: types.CallbackQuery, pool):
    try:
        _, attacker_id, victim_id = callback.data.split(":")
        attacker_id = int(attacker_id)
        victim_id = int(victim_id)
    except (ValueError, IndexError):
        return await callback.answer("❌ Ошибка данных", show_alert=True)

    # Нажимать может только жертва (та, кому пришло СБ)
    if callback.from_user.id != victim_id:
        return await callback.answer("❌ Это не твоё сообщение!", show_alert=True)

    try:
        async with pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                # Информация об атакующем
                await cur.execute(
                    "SELECT l.lab_id, l.lab_name, l.pathogen_name, l.bio_experience, "
                    "       u.username, u.full_name "
                    "FROM Lab l LEFT JOIN Users u ON u.id = l.lab_id "
                    "WHERE l.lab_id = %s",
                    (attacker_id,)
                )
                row = await cur.fetchone()

                if not row:
                    return await callback.answer("❌ Игрок не найден", show_alert=True)

                # Сколько он приносит как жертва (для вызывающего)
                await cur.execute(
                    "SELECT victim_bio_resource_earn FROM Victims "
                    "WHERE victims_owner_id = %s AND victim_id = %s",
                    (callback.from_user.id, attacker_id)
                )
                victim_row = await cur.fetchone()
                earn = int(victim_row["victim_bio_resource_earn"]) if victim_row else 0

                # Сколько он стоит как жертва (если бы заразили)
                await cur.execute(
                    "SELECT bio_experience FROM Lab WHERE lab_id = %s",
                    (attacker_id,)
                )
                exp_row = await cur.fetchone()
                bio_exp = int(exp_row["bio_experience"]) if exp_row else 0
    except Exception as e:
        logger.error(f"[SB_CHECK ERROR] {e}")
        return await callback.answer("❌ Ошибка", show_alert=True)

    uname = row.get("username")
    full_name = row.get("full_name") or uname or str(attacker_id)

    # Показываем во всплывающем окне (без HTML, лимит 200 символов)
    text = (
        f"👤 {full_name}\n"
        f"🆔 ID: {attacker_id}\n\n"
        f"💰 Приносит: {earn:,} 🧬"
    )

    if len(text) > 195:
        text = text[:190] + "..."

    await callback.answer(text, show_alert=True)


@router.callback_query(F.data.startswith("sb_infect:"))
async def cb_sb_infect(callback: types.CallbackQuery, bot: Bot, db,
                       repo_biowar: RequestsRepoBiowar,
                       redis: Redis, lock: Lock, pool):
    try:
        _, attacker_id, victim_id = callback.data.split(":")
        attacker_id = int(attacker_id)
        victim_id = int(victim_id)
    except (ValueError, IndexError):
        return await callback.answer("❌ Ошибка данных", show_alert=True)

    if callback.from_user.id != victim_id:
        return await callback.answer("❌ Это не твоё сообщение!", show_alert=True)

    from core.handlers.biowar.infects.infect import infect

    fake_message = callback.message.model_copy(update={
        'from_user': callback.from_user,
        'text': f'заразить {attacker_id} 1',
        'reply_to_message': None,
        'entities': None,
        'caption_entities': None,
    })
    setattr(fake_message, '_override_target_id', attacker_id)

    await callback.answer("⚔️ Атакую!")
    try:
        await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar,
                     redis=redis, lock=lock)
    except Exception as e:
        logger.error(f"[SB_INFECT ERROR] {e}")


@router.callback_query(F.data.startswith("fever_heal:"))
async def cb_fever_heal(callback: types.CallbackQuery, bot: Bot, db,
                        redis: Redis, repo_biowar: RequestsRepoBiowar):
    try:
        owner_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        return await callback.answer("❌ Ошибка", show_alert=True)

    if callback.from_user.id != owner_id:
        return await callback.answer("❌ Это не твоё сообщение!", show_alert=True)

    from core.handlers.biowar.infects.infect_addons import buy_vaccine

    fake_message = callback.message.model_copy(update={
        'from_user': callback.from_user,
        'text': 'кв',
        'reply_to_message': None,
    })

    try:
        await buy_vaccine(fake_message, bot, db, redis, repo_biowar)
        await callback.answer("💊 Вакцина куплена!")
        try:
            await callback.message.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"[FEVER HEAL ERROR] {e}")
        await callback.answer("❌ Ошибка при лечении", show_alert=True)

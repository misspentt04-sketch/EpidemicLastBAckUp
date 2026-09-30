import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.cursors import DictCursor

from core.utils.db_api.settings_pool import db_pool

router = Router()
logger = logging.getLogger(__name__)

SPOILER_HIDDEN = "Хуй тебе!"


async def _collect_stats(user_id: int):
    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            # 1. Жертвы
            await cur.execute(
                "SELECT COUNT(*) AS cnt FROM Victims WHERE victims_owner_id = %s",
                (user_id,)
            )
            row = await cur.fetchone()
            victims = int(row.get("cnt") if row and row.get("cnt") is not None else 0)

            # 2. Уровень РБ
            await cur.execute(
                "SELECT rebirth_level FROM Lab WHERE lab_id = %s", (user_id,)
            )
            row = await cur.fetchone()
            rebirth = int(row.get("rebirth_level") if row and row.get("rebirth_level") is not None else 0)

            # Сумма ресурсов со всех жертв * (1 + rebirth_level * 0.10)
            await cur.execute(
                "SELECT COALESCE(SUM(victim_bio_resource_earn), 0) AS s "
                "FROM Victims WHERE victims_owner_id = %s",
                (user_id,)
            )
            row = await cur.fetchone()
            tick_base = int(row.get("s") if row and row.get("s") is not None else 0)
            tick_income = int(tick_base * (1 + rebirth * 0.10))

            # 3. Заражения за сегодня
            await cur.execute(
                "SELECT COUNT(*) AS total, "
                "       COUNT(DISTINCT victim_id) AS uniq "
                "FROM biowar_infection_history "
                "WHERE attacker_id = %s AND DATE(infect_date) = CURDATE()",
                (user_id,)
            )
            row = await cur.fetchone()
            total_today = int(row.get("total") if row and row.get("total") is not None else 0)
            uniq_today = int(row.get("uniq") if row and row.get("uniq") is not None else 0)

    return victims, tick_income, rebirth, total_today, uniq_today


def _make_text(victims, tick_income, rebirth, total_today, uniq_today, revealed: bool):
    if revealed:
        bio_line = f"🧬 <b>Био-ресурсов:</b> <code>{tick_income:,}</code>"
    else:
        bio_line = f"🧬 <b>Био-ресурсов:</b> <tg-spoiler>{SPOILER_HIDDEN}</tg-spoiler>"

    return (
        f"📊 <b>Количество жертв:</b> <code>{victims:,}</code>\n"
        f"{bio_line}\n"
        f"🎚 <b>Уровень РБ:</b> <code>{rebirth}</code>\n\n"
        f"<blockquote><b>Заражений за день:</b>\n"
        f"🦠 {total_today} | 🆕 {uniq_today}</blockquote>"
    )


def _make_kb(author_id: int, revealed: bool) -> InlineKeyboardMarkup:
    toggle_text = "🙈 Скрыть" if revealed else "👁 Показать"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=toggle_text, callback_data=f"bio_toggle:{author_id}"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data=f"bio_close:{author_id}"),
    ]])


@router.message(F.text.lower().regexp(r'^[.!\/]?(биостат|мое инфо|инфо)\s*$'))
async def cmd_bio_stats(msg: types.Message):
    user_id = msg.from_user.id
    try:
        victims, tick_income, rebirth, total_today, uniq_today = await _collect_stats(user_id)
    except Exception as e:
        logger.error(f"[BIO_STATS ERROR] {e}")
        return await msg.answer("❌ Не удалось получить статистику. Попробуйте позже.")

    text = _make_text(victims, tick_income, rebirth, total_today, uniq_today, revealed=False)
    kb = _make_kb(user_id, revealed=False)

    await msg.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("bio_toggle:"))
async def cb_bio_toggle(callback: types.CallbackQuery):
    try:
        author_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        return await callback.answer("❌ Ошибка", show_alert=True)

    if callback.from_user.id != author_id:
        return await callback.answer("❌ Это не твоё сообщение!", show_alert=True)

    try:
        current_btn = callback.message.reply_markup.inline_keyboard[0][0].text
    except Exception:
        current_btn = "👁 Показать"

    revealed = current_btn.strip() == "🙈 Скрыть"
    new_revealed = not revealed

    try:
        victims, tick_income, rebirth, total_today, uniq_today = await _collect_stats(author_id)
    except Exception as e:
        logger.error(f"[BIO_STATS TOGGLE ERROR] {e}")
        return await callback.answer("❌ Ошибка при получении данных", show_alert=True)

    text = _make_text(victims, tick_income, rebirth, total_today, uniq_today, revealed=new_revealed)
    kb = _make_kb(author_id, revealed=new_revealed)

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass

    await callback.answer()


@router.callback_query(F.data.startswith("bio_close:"))
async def cb_bio_close(callback: types.CallbackQuery):
    try:
        author_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        return await callback.answer("❌ Ошибка", show_alert=True)

    if callback.from_user.id != author_id:
        return await callback.answer("❌ Это не твоё сообщение!", show_alert=True)

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()

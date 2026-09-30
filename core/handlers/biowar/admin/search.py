import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asyncmy.cursors import DictCursor

from core.settings import settings

router = Router()
logger = logging.getLogger(__name__)

LOG_CHAT_ID = -1003688648228
MAX_RESULTS = 4


def _is_admin(user_id: int) -> bool:
    return str(user_id) in settings.bots.admin_id


async def _do_search(pool, field: str, text: str):
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                f"SELECT lab_id, lab_name, pathogen_name, bio_experience "
                f"FROM Lab WHERE {field} LIKE %s AND {field} IS NOT NULL "
                f"LIMIT %s",
                (f"%{text}%", MAX_RESULTS)
            )
            return await cur.fetchall()


def _format_results(field: str, text: str, rows: list) -> str:
    if field == "lab_name":
        header = f'🔍 <b>Поиск по лабораториям:</b> «{text}»'
    else:
        header = f'🔍 <b>Поиск по патогенам:</b> «{text}»'

    if not rows:
        return header + "\n\n📭 Ничего не найдено."

    lines = [header, f"<b>Найдено:</b> {len(rows)}", ""]

    for i, row in enumerate(rows, 1):
        lab_id = row["lab_id"]
        name = row.get(field) or "—"
        lab_name = row.get("lab_name") or "—"
        pathogen = row.get("pathogen_name") or "—"
        bio_exp = row.get("bio_experience") or 0

        if field == "lab_name":
            title = name
            extra = f"патоген: <i>{pathogen}</i>"
        else:
            title = name
            extra = f"лаб: <i>{lab_name}</i>"

        lines.append(
            f"{i}. <a href='tg://user?id={lab_id}'>{title}</a>\n"
            f"   👤 ID: <code>{lab_id}</code>\n"
            f"   🔬 {extra} | ⚡ {bio_exp:,} XP\n"
        )

    return "\n".join(lines)


def _make_kb(rows: list) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for r in rows:
        lab_id = r["lab_id"]
        row.append(InlineKeyboardButton(text=f"👤 {lab_id}", callback_data=f"search_open:{lab_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text.regexp(r'(?i)^поиск\s+имя\s+.+'))
async def search_lab(msg: types.Message, pool):
    if not _is_admin(msg.from_user.id):
        return

    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        return await msg.answer("❌ Формат: <code>поиск имя &lt;текст&gt;</code>", parse_mode="HTML")

    text = parts[2].strip()
    if len(text) < 2:
        return await msg.answer("❌ Введите минимум 2 символа для поиска.")

    rows = await _do_search(pool, "lab_name", text)
    text_out = _format_results("lab_name", text, rows)
    kb = _make_kb(rows) if rows else None

    await msg.answer(text_out, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb)


@router.message(F.text.regexp(r'(?i)^поиск\s+пат\s+.+'))
async def search_pathogen(msg: types.Message, pool):
    if not _is_admin(msg.from_user.id):
        return

    parts = msg.text.split(maxsplit=2)
    if len(parts) < 3:
        return await msg.answer("❌ Формат: <code>поиск пат &lt;текст&gt;</code>", parse_mode="HTML")

    text = parts[2].strip()
    if len(text) < 2:
        return await msg.answer("❌ Введите минимум 2 символа для поиска.")

    rows = await _do_search(pool, "pathogen_name", text)
    text_out = _format_results("pathogen_name", text, rows)
    kb = _make_kb(rows) if rows else None

    await msg.answer(text_out, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb)


@router.callback_query(F.data.startswith("search_open:"))
async def search_open_profile(callback: types.CallbackQuery, pool):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("❌ Только для админов!", show_alert=True)

    try:
        lab_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        return await callback.answer("❌ Ошибка данных", show_alert=True)

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT l.lab_id, l.lab_name, l.pathogen_name, l.bio_experience, "
                "l.bio_resource, l.infect, l.immunity, l.lethality, l.security_service, "
                "l.science, l.pathogens, l.ready_pathogens, "
                "u.username, u.full_name "
                "FROM Lab l LEFT JOIN Users u ON u.id = l.lab_id "
                "WHERE l.lab_id = %s",
                (lab_id,)
            )
            row = await cur.fetchone()

    if not row:
        return await callback.answer("❌ Игрок не найден", show_alert=True)

    name_line = (
        f'<a href="https://t.me/{row["username"]}">{row["full_name"] or row["username"]}</a>'
        if row.get("username") else f'<a href="tg://user?id={lab_id}">{row["full_name"] or lab_id}</a>'
    )

    text = (
        f"👤 <b>Игрок:</b> {name_line}\n"
        f"🆔 <b>ID:</b> <code>{lab_id}</code>\n\n"
        f"🧪 <b>Лаборатория:</b> {row['lab_name'] or '—'}\n"
        f"☣️ <b>Патоген:</b> {row['pathogen_name'] or '—'}\n\n"
        f"⚡ <b>Био-опыт:</b> {row['bio_experience']:,}\n"
        f"🧬 <b>Био-ресурс:</b> {row['bio_resource']:,}\n\n"
        f"🎯 Заразность: <b>{row['infect']}</b>\n"
        f"🛡 Иммунитет: <b>{row['immunity']}</b>\n"
        f"☠️ Летальность: <b>{row['lethality']}</b>\n"
        f"🔒 Безопасность: <b>{row['security_service']}</b>\n"
        f"🧪 Разработка: <b>{row['science']}</b>\n"
        f"🧬 Патогены: <b>{row['ready_pathogens']}</b> / <b>{row['pathogens']}</b>"
    )

    await callback.message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()

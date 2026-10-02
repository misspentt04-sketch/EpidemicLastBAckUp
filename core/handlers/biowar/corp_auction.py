import time
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncmy.cursors import DictCursor

from core.settings import settings
from core.utils.db_api.settings_pool import db_pool

router = Router()
logger = logging.getLogger(__name__)

MSK = timezone(timedelta(hours=3))
LOG_CHAT_ID = -1004335676077
AUCTION_DURATION = 10 * 60          # 10 минут
START_INTERVAL = 3 * 3600           # каждые 3 часа
START_MINUTE = 10                   # в HH:10
BASE_SLOTS = 50                     # стартовый лимит
MAX_SLOTS = 100                     # максимум


class SlotStates(StatesGroup):
    waiting_bid = State()


# ===== ВРЕМЯ =====

def _next_start_ts() -> int:
    """Ближайший HH:10 по МСК, кратный 3 часам (00:10, 03:10, 06:10 ...)."""
    now_msk = datetime.now(MSK)
    # Ближайший час с шагом 3
    h = now_msk.hour
    target_hour = (h // 3) * 3
    candidate = now_msk.replace(minute=START_MINUTE, second=0, microsecond=0, hour=target_hour)
    if candidate <= now_msk:
        # взять следующий
        candidate = candidate + timedelta(hours=3)
    return int(candidate.timestamp())


# ===== БД =====

async def _get_active_auction():
    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM CorpSlotAuctions WHERE status='active' ORDER BY id DESC LIMIT 1"
            )
            return await cur.fetchone()


async def _create_auction(start_at: int | None = None) -> int:
    pool = await db_pool.get_pool()
    now = int(time.time())
    if start_at is None:
        start_at = _next_start_ts()
    end_at = start_at + AUCTION_DURATION
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO CorpSlotAuctions (start_at, end_at, status, created_at) "
                "VALUES (%s, %s, 'active', %s)",
                (start_at, end_at, now)
            )
            return cur.lastrowid


async def _get_top_bids(auction_id: int, limit: int = 5):
    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute("""
                SELECT b.bidder_id, b.corp_code, b.bid_total, b.created_at,
                       u.username, u.full_name, c.name AS corp_name
                FROM CorpSlotBids b
                LEFT JOIN Users u ON u.id = b.bidder_id
                LEFT JOIN Corporation c ON c.invitation_code = b.corp_code
                WHERE b.auction_id = %s
                ORDER BY b.bid_total DESC, b.created_at ASC
                LIMIT %s
            """, (auction_id, limit))
            return await cur.fetchall()


async def _get_user_bid(auction_id: int, user_id: int):
    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM CorpSlotBids WHERE auction_id=%s AND bidder_id=%s",
                (auction_id, user_id)
            )
            return await cur.fetchone()


async def close_auction(auction_id: int, bot: Bot | None = None):
    """Закрывает аукцион, определяет победителя, начисляет слот, анонсирует."""
    pool = await db_pool.get_pool()

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            # активный аукцион?
            await cur.execute(
                "SELECT * FROM CorpSlotAuctions WHERE id=%s AND status='active'",
                (auction_id,)
            )
            auction = await cur.fetchone()
            if not auction:
                return

            # победитель
            await cur.execute("""
                SELECT b.*, c.name AS corp_name, u.full_name, u.username
                FROM CorpSlotBids b
                LEFT JOIN Corporation c ON c.invitation_code = b.corp_code
                LEFT JOIN Users u ON u.id = b.bidder_id
                WHERE b.auction_id = %s
                ORDER BY b.bid_total DESC, b.created_at ASC
                LIMIT 1
            """, (auction_id,))
            winner = await cur.fetchone()

            if not winner:
                # нет ставок — закрываем пусто
                await cur.execute(
                    "UPDATE CorpSlotAuctions SET status='finished' WHERE id=%s",
                    (auction_id,)
                )
                print(f"[AUCTION] #{auction_id} закрыт без ставок")
                return

            bidder_id = winner['bidder_id']
            corp_code = winner['corp_code']
            bid_total = winner['bid_total']

            # списываем у победителя
            await cur.execute(
                "UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s",
                (bid_total, bidder_id)
            )

            # попытка выдать слот
            await cur.execute(
                "SELECT members, bonus_slots FROM Corporation WHERE invitation_code=%s",
                (corp_code,)
            )
            corp = await cur.fetchone()

            slot_granted = 0
            if corp:
                current = int(corp['members'] or 0) + int(corp['bonus_slots'] or 0)
                if current < MAX_SLOTS:
                    await cur.execute(
                        "UPDATE Corporation SET bonus_slots = bonus_slots + 1 WHERE invitation_code=%s",
                        (corp_code,)
                    )
                    slot_granted = 1

            await cur.execute("""
                UPDATE CorpSlotAuctions
                SET status='finished',
                    winner_bidder_id=%s,
                    winner_corp_code=%s,
                    winner_bid=%s,
                    slot_granted=%s
                WHERE id=%s
            """, (bidder_id, corp_code, bid_total, slot_granted, auction_id))

    # уведомления и анонс
    winner_name = winner.get('full_name') or winner.get('username') or str(bidder_id)
    corp_name = winner.get('corp_name') or corp_code

    if slot_granted:
        status_line = f"✅ Слот выдан корпорации «{corp_name}»"
    else:
        status_line = f"⚠️ У корпорации уже {MAX_SLOTS} слотов — слот не выдан, ресурсы списаны"

    text = (
        f"🏆 <b>Аукцион на слот завершён!</b>\n\n"
        f"👤 Победитель: <a href='tg://user?id={bidder_id}'>{winner_name}</a>\n"
        f"🏛 Корпорация: <b>«{corp_name}»</b>\n"
        f"💰 Сумма ставки: <b>{bid_total:,}</b> 🧬\n"
        f"{status_line}"
    ).replace(",", " ")

    if bot is not None:
        try:
            await bot.send_message(LOG_CHAT_ID, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            print(f"[AUCTION NOTIFY ERROR] {e}")

    print(f"[AUCTION] #{auction_id} закрыт. Победитель {bidder_id} ({corp_code}) — {bid_total}, slot={slot_granted}")


async def announce_start(bot: Bot):
    text = (
        "🕐 <b>Аукцион на слот корпорации начался!</b>\n\n"
        f"⏳ Длительность: <b>10 минут</b>\n"
        f"💰 Ставка: био-ресурсы 🧬\n"
        f"📈 Можно повышать ставку, суммы складываются\n\n"
        f"Команда: <code>!слот</code> — текущий аукцион\n"
        f"Ставка: <code>!слот ставка N</code>"
    )
    try:
        await bot.send_message(LOG_CHAT_ID, text, parse_mode="HTML")
    except Exception as e:
        print(f"[AUCTION ANNOUNCE ERROR] {e}")


# ===== ФОНОВАЯ ЗАДАЧА =====

async def corp_slot_auction_loop(bot: Bot):
    """Раз в 30 сек — создаёт и закрывает аукционы."""
    print("[AUCTION] loop запущен")
    while True:
        try:
            now = int(time.time())
            active = await _get_active_auction()

            # закрытие
            if active and now >= active['end_at']:
                await close_auction(active['id'], bot)

            # старт нового
            active = await _get_active_auction()
            if not active:
                next_start = _next_start_ts()
                # если время старта уже почти наступило (в пределах 30 сек) — создаём
                if now >= next_start - 30:
                    # сдвигаем старт на ближайший корректный
                    aid = await _create_auction(start_at=next_start)
                    await announce_start(bot)
                    print(f"[AUCTION] создан #{aid}, start={next_start}")

        except Exception as e:
            print(f"[AUCTION LOOP ERROR] {e}")

        await __import__('asyncio').sleep(30)


# ===== КОМАНДЫ =====

def _fmt(n: int) -> str:
    return f"{int(n):,}".replace(",", " ")


@router.message(F.text.lower().regexp(r'^[.!\/]?слот\s*$'))
async def cmd_slot(msg: types.Message):
    auction = await _get_active_auction()
    if not auction:
        return await msg.answer("❌ Сейчас нет активного аукциона. Следующий — по расписанию (HH:10 каждые 3 часа).")

    now = int(time.time())
    left = max(0, auction['end_at'] - now)
    m = left // 60
    s = left % 60

    top = await _get_top_bids(auction['id'], 5)

    lines = [f"💠 <b>Аукцион на слот корпорации</b>\n"]
    lines.append(f"⏳ Осталось: <b>{m}м {s}с</b>\n")

    if top:
        lines.append("🏆 <b>Топ-5:</b>")
        for i, t in enumerate(top, 1):
            name = t.get('full_name') or t.get('username') or str(t['bidder_id'])
            corp = t.get('corp_name') or t.get('corp_code')
            lines.append(f"{i}. <a href='tg://user?id={t['bidder_id']}'>{name}</a> — <b>{_fmt(t['bid_total'])}</b> 🧬 (корпа «{corp}»)")
    else:
        lines.append("📭 Пока нет ставок.")

    # своя ставка и отставание от топ-5
    user_bid = await _get_user_bid(auction['id'], msg.from_user.id)
    if user_bid:
        lines.append(f"\n💼 Ваша сумма: <b>{_fmt(user_bid['bid_total'])}</b> 🧬")
    if len(top) >= 5:
        threshold = top[4]['bid_total']
        need = max(0, threshold + 1 - (user_bid['bid_total'] if user_bid else 0))
        lines.append(f"📈 До топ-5: <b>{_fmt(need)}</b> 🧬")

    await msg.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text.lower().regexp(r'^[.!\/]?слот\s+топ\s*$'))
async def cmd_slot_top(msg: types.Message):
    await cmd_slot(msg)


@router.message(F.text.lower().regexp(r'^[.!\/]?слот\s+инфо\s*$'))
async def cmd_slot_info(msg: types.Message):
    await msg.answer(
        "📖 <b>Правила аукциона на слот корпорации</b>\n\n"
        f"• Старт: <b>HH:10 МСК</b> каждые 3 часа\n"
        f"• Длительность: <b>10 минут</b>\n"
        f"• Разыгрывается <b>1 слот</b>\n"
        f"• Ставка: <b>био-ресурсы 🧬</b>\n"
        f"• Минимум: <b>1 🧬</b>\n"
        f"• Ставки <b>суммируются</b> — можно повышать\n"
        f"• Победитель — <b>максимальная сумма</b>\n"
        f"• Ничья — побеждает <b>ранняя</b> ставка\n\n"
        f"Команды:\n"
        f"<code>!слот</code> — текущий аукцион\n"
        f"<code>!слот ставка N</code> — поставить N\n"
        f"<code>!слот топ</code> — топ-5\n",
        parse_mode="HTML"
    )


@router.message(F.text.lower().regexp(r'^[.!\/]?слот\s+ставка\s+(\d+)\s*$'))
async def cmd_slot_bid(msg: types.Message):
    import re
    m = re.search(r'ставка\s+(\d+)', msg.text, re.IGNORECASE)
    if not m:
        return await msg.answer("❌ Формат: <code>!слот ставка 1000</code>", parse_mode="HTML")

    amount = int(m.group(1))
    if amount < 1:
        return await msg.answer("❌ Минимум 1 🧬.")

    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            # корпа игрока
            await cur.execute(
                "SELECT corporation_code FROM CorporationMembers WHERE member_id=%s LIMIT 1",
                (msg.from_user.id,)
            )
            cm = await cur.fetchone()
            if not cm:
                return await msg.answer("❌ Вы не состоите в корпорации.")
            corp_code = cm['corporation_code']

            # активный аукцион
            await cur.execute(
                "SELECT * FROM CorpSlotAuctions WHERE status='active' ORDER BY id DESC LIMIT 1"
            )
            auction = await cur.fetchone()
            if not auction:
                return await msg.answer("❌ Сейчас нет активного аукциона.")

            now = int(time.time())
            if now < auction['start_at']:
                return await msg.answer("⏳ Аукцион ещё не начался.")
            if now >= auction['end_at']:
                return await msg.answer("⏳ Аукцион уже закончился.")

            # баланс
            await cur.execute(
                "SELECT bio_resource FROM Lab WHERE lab_id=%s", (msg.from_user.id,)
            )
            lab = await cur.fetchone()
            if not lab:
                return await msg.answer("❌ У вас нет лаборатории.")
            balance = int(lab['bio_resource'] or 0)

            # текущая ставка игрока
            await cur.execute(
                "SELECT * FROM CorpSlotBids WHERE auction_id=%s AND bidder_id=%s",
                (auction['id'], msg.from_user.id)
            )
            prev = await cur.fetchone()

            if prev:
                if amount < 1:
                    return await msg.answer("❌ Минимум +1 🧬.")
                new_total = prev['bid_total'] + amount
                # === ГЛАВНАЯ ПРОВЕРКА: общая сумма ставки не больше баланса ===
                if new_total > balance:
                    return await msg.answer(
                        f"❌ Общая сумма ставки не может превышать ваш баланс!\n"
                        f"💰 Баланс: <b>{_fmt(balance)}</b> 🧬\n"
                        f"💼 Текущая ставка: <b>{_fmt(prev['bid_total'])}</b> 🧬\n"
                        f"📈 Максимум можно добавить: <b>{_fmt(balance - prev['bid_total'])}</b> 🧬",
                        parse_mode="HTML",
                    )
                await cur.execute(
                    "UPDATE CorpSlotBids SET bid_total=%s, updated_at=%s WHERE id=%s",
                    (new_total, now, prev['id'])
                )
                added = amount
            else:
                if amount > balance:
                    return await msg.answer(
                        f"❌ Ставка не может превышать ваш баланс!\n"
                        f"💰 Баланс: <b>{_fmt(balance)}</b> 🧬",
                        parse_mode="HTML",
                    )
                new_total = amount
                await cur.execute(
                    "INSERT INTO CorpSlotBids (auction_id, bidder_id, corp_code, bid_total, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (auction['id'], msg.from_user.id, corp_code, new_total, now, now)
                )
                added = amount

    await msg.answer(
        f"✅ Ставка принята!\n"
        f"➕ Добавлено: <b>{_fmt(added)}</b> 🧬\n"
        f"💼 Ваша сумма: <b>{_fmt(new_total)}</b> 🧬",
        parse_mode="HTML"
    )


# ===== АДМИН =====

def _is_admin(user_id: int) -> bool:
    return str(user_id) in settings.bots.admin_id


@router.message(F.text.lower().regexp(r'^[.!\/]?слот\s+старт\s*$'))
async def cmd_slot_admin_start(msg: types.Message, bot: Bot):
    if not _is_admin(msg.from_user.id):
        return
    active = await _get_active_auction()
    if active:
        return await msg.answer("⚠️ Уже есть активный аукцион.")
    now = int(time.time())
    aid = await _create_auction(start_at=now)
    await announce_start(bot)
    await msg.answer(f"✅ Аукцион #{aid} запущен вручную.")


@router.message(F.text.lower().regexp(r'^[.!\/]?слот\s+отмена\s*$'))
async def cmd_slot_admin_cancel(msg: types.Message, bot: Bot):
    if not _is_admin(msg.from_user.id):
        return
    active = await _get_active_auction()
    if not active:
        return await msg.answer("⚠️ Нет активного аукциона.")
    pool = await db_pool.get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE CorpSlotAuctions SET status='cancelled' WHERE id=%s",
                (active['id'],)
            )
    try:
        await bot.send_message(LOG_CHAT_ID, f"❌ Аукцион #{active['id']} отменён администратором.", parse_mode="HTML")
    except Exception:
        pass
    await msg.answer(f"✅ Аукцион #{active['id']} отменён.")

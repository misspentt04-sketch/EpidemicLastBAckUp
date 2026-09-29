import secrets
import string
import time
from datetime import datetime, timedelta, timezone


CODE_LEN = 10
CODE_ALPHABET = string.ascii_lowercase + string.digits
MSK = timezone(timedelta(hours=3))


def _gen_code() -> str:
    return ''.join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))


def _next_msk_midnight_ts() -> int:
    """Возвращает timestamp ближайшего 00:00 по МСК."""
    now_msk = datetime.now(MSK)
    tomorrow = (now_msk + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int(tomorrow.timestamp())


async def get_or_create_referral_link(pool, referrer_id: int) -> tuple[str, int]:
    """
    Возвращает (code, expires_at).
    Если активная ссылка есть — вернёт её. Если нет — создаст новую.
    Ссылка всегда истекает в ближайшие 00:00 по МСК.
    """
    now = int(time.time())
    expires_at = _next_msk_midnight_ts()

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 1. Удаляем все истёкшие ссылки этого игрока
            await cur.execute(
                "DELETE FROM ReferralLinks WHERE referrer_id = %s AND expires_at < %s",
                (referrer_id, now)
            )

            # 2. Ищем активную
            await cur.execute(
                "SELECT code, expires_at FROM ReferralLinks WHERE referrer_id = %s ORDER BY expires_at DESC LIMIT 1",
                (referrer_id,)
            )
            row = await cur.fetchone()
            if row:
                if isinstance(row, dict):
                    return row['code'], row['expires_at']
                return row[0], row[1]

            # 3. Создаём новую
            for _ in range(5):
                code = _gen_code()
                try:
                    await cur.execute(
                        "INSERT INTO ReferralLinks (code, referrer_id, created_at, expires_at) VALUES (%s, %s, %s, %s)",
                        (code, referrer_id, now, expires_at)
                    )
                    return code, expires_at
                except Exception:
                    continue

            raise RuntimeError("Не удалось сгенерировать уникальный код")


async def resolve_referral_code(pool, code: str) -> int | None:
    """Возвращает referrer_id по коду, если код активен. Иначе None."""
    if not code:
        return None
    now = int(time.time())
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT referrer_id, expires_at FROM ReferralLinks WHERE code = %s",
                (code,)
            )
            row = await cur.fetchone()
            if not row:
                return None
            if isinstance(row, dict):
                referrer_id = row['referrer_id']
                expires_at = row['expires_at']
            else:
                referrer_id, expires_at = row[0], row[1]
            if expires_at < now:
                return None
            return int(referrer_id)

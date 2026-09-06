from asyncmy.cursors import Cursor

async def is_player_hidden(lab_id: int, cur: Cursor) -> bool:
    """Проверяет, скрыт ли игрок в топах"""
    await cur.execute("SELECT 1 FROM HiddenPlayers WHERE lab_id = %s;", (lab_id,))
    result = await cur.fetchone()
    return result is not None

async def get_visible_players(cur: Cursor) -> list:
    """Возвращает список видимых игроков"""
    await cur.execute("SELECT lab_id FROM Lab WHERE lab_id NOT IN (SELECT lab_id FROM HiddenPlayers);")
    rows = await cur.fetchall()
    return [row[0] for row in rows] if rows else []

async def hide_player(lab_id: int, hidden_by: int, cur: Cursor):
    """Скрывает игрока"""
    await cur.execute("""
        INSERT INTO HiddenPlayers (lab_id, hidden_by)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE hidden_by = VALUES(hidden_by), hidden_at = UNIX_TIMESTAMP()
    """, (lab_id, hidden_by))

async def show_player(lab_id: int, cur: Cursor):
    """Показывает игрока"""
    await cur.execute("DELETE FROM HiddenPlayers WHERE lab_id = %s;", (lab_id,))

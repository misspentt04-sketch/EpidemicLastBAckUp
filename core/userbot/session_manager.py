import os
import asyncio
import logging
from pathlib import Path
from pyrogram import Client
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
ACTIVE_CLIENTS: Dict[str, Client] = {}

def init_sessions_dir():
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Папка для сессий: {SESSIONS_DIR}")
        return True
    except Exception as e:
        logger.error(f"Ошибка создания папки: {e}")
        return False

def save_session(username: str, session_string: str):
    try:
        init_sessions_dir()
        file_path = SESSIONS_DIR / f"{username}.session"
        with open(file_path, 'w') as f:
            f.write(session_string)
        logger.info(f"Сессия сохранена: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

def load_session(username: str) -> Optional[str]:
    try:
        file_path = SESSIONS_DIR / f"{username}.session"
        if file_path.exists():
            with open(file_path, 'r') as f:
                return f.read()
        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        return None

def get_all_sessions() -> List[str]:
    try:
        sessions = []
        if SESSIONS_DIR.exists():
            for file_path in SESSIONS_DIR.glob("*.session"):
                sessions.append(file_path.stem)
        return sessions
    except Exception as e:
        logger.error(f"Ошибка списка сессий: {e}")
        return []

def delete_session(username: str) -> bool:
    try:
        file_path = SESSIONS_DIR / f"{username}.session"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Сессия удалена: {username}")
            return True
        return False
    except Exception as e:
        logger.error(f"Ошибка удаления: {e}")
        return False

async def get_client(username: str) -> Optional[Client]:
    if username in ACTIVE_CLIENTS and ACTIVE_CLIENTS[username].is_connected:
        return ACTIVE_CLIENTS[username]
    
    session_string = load_session(username)
    if not session_string:
        logger.error(f"Сессия для {username} не найдена")
        return None
    
    try:
        client = Client(
            name=f"userbot_{username}",
            session_string=session_string,
            api_id=29154972,
            api_hash="cc13cd6917234b587cf47048ba69072d"
        )
        await client.connect()
        ACTIVE_CLIENTS[username] = client
        logger.info(f"Клиент {username} подключен")
        return client
    except Exception as e:
        logger.error(f"Ошибка подключения клиента {username}: {e}")
        return None

async def send_message_with_delay(
    client: Client,
    target: str,
    text: str,
    delay: float = 0.33,
    reply_to_message_id: int = None
):
    try:
        if reply_to_message_id:
            await client.send_message(
                chat_id=target,
                text=text,
                reply_to_message_id=reply_to_message_id
            )
        else:
            await client.send_message(
                chat_id=target,
                text=text
            )
        await asyncio.sleep(delay)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return False

async def disconnect_all_clients():
    for username, client in ACTIVE_CLIENTS.items():
        try:
            if client.is_connected:
                await client.disconnect()
        except:
            pass
    ACTIVE_CLIENTS.clear()
    logger.info("Все клиенты отключены")

async def save_telethon_session(username: str, session_string: str):
    """Сохраняет сессию Telethon в data/sessions/"""
    try:
        from pathlib import Path
        SESSIONS_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        
        file_path = SESSIONS_DIR / f"{username}.session"
        with open(file_path, 'w') as f:
            f.write(session_string)
        logger.info(f"✅ Telethon сессия сохранена: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

async def load_telethon_session(username: str):
    """Загружает сессию Telethon из data/sessions/"""
    try:
        from pathlib import Path
        SESSIONS_DIR = Path(__file__).parent.parent.parent / "data" / "sessions"
        file_path = SESSIONS_DIR / f"{username}.session"
        if file_path.exists():
            with open(file_path, 'r') as f:
                return f.read()
        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        return None


def get_ordered_sessions():
    """Возвращает сессии в правильном порядке"""
    import json
    import os
    
    ORDER_FILE = "data/sessions_order.json"
    
    try:
        if os.path.exists(ORDER_FILE):
            with open(ORDER_FILE, 'r') as f:
                order = json.load(f)
        else:
            order = []
    except:
        order = []
    
    all_sessions = get_all_sessions()
    
    if order:
        ordered = [s for s in order if s in all_sessions]
        for s in all_sessions:
            if s not in ordered:
                ordered.append(s)
        return ordered
    return all_sessions

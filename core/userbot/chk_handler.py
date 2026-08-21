import asyncio
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

from .session_manager import (
    get_all_sessions,
    load_telethon_session,
    get_ordered_sessions
)

logger = logging.getLogger(__name__)

router = Router()

ADMIN_IDS = [1758346431, 7972320837]
API_ID = 29154972
API_HASH = "cc13cd6917234b587cf47048ba69072d"

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ===== Глобальные клиенты =====
GLOBAL_CLIENTS = {}

async def get_or_create_client(username: str):
    global GLOBAL_CLIENTS
    if username in GLOBAL_CLIENTS:
        client = GLOBAL_CLIENTS[username]
        try:
            if client.is_connected():
                return client
        except:
            pass
    session_string = await load_telethon_session(username)
    if not session_string:
        return None
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await client.connect()
    GLOBAL_CLIENTS[username] = client
    return client

# ===== БД =====
DB_PATH = Path(__file__).parent.parent.parent / "data" / "victims.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS victims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attacker_username TEXT NOT NULL,
            attacker_id INTEGER NOT NULL,
            victim_id INTEGER,
            victim_username TEXT,
            bio_earn INTEGER DEFAULT 0,
            infected_date TEXT,
            expire_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

async def get_username_by_id(client, user_id: int) -> str:
    """Получает username по ID"""
    try:
        entity = await client.get_entity(user_id)
        if hasattr(entity, 'username') and entity.username:
            return entity.username
        elif hasattr(entity, 'first_name'):
            return entity.first_name
    except:
        pass
    return str(user_id)

def get_victims(attacker_username: str) -> list:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT victim_username, bio_earn, expire_date, victim_id
            FROM victims 
            WHERE attacker_username = ? AND expire_date > datetime('now')
            ORDER BY expire_date ASC
        """, (attacker_username,))
        victims = cursor.fetchall()
        conn.close()
        return victims
    except:
        return []

# ===== Команда ТК =====
@router.message(F.text.lower().startswith("тк"))
async def cmd_tk(msg: Message):
    global INFECTION_RUNNING
    
    if not is_admin(msg.from_user.id):
        return
    
    # Проверяем флаг
    try:
        from core.userbot.userbot_manager import INFECTION_RUNNING as INF_FLAG, get_stop_flag
        if INF_FLAG:
            await msg.answer("⚠️ Заражение уже запущено! Дождитесь окончания.")
            return
        if get_stop_flag():
            await msg.answer("⏹️ Команды остановлены! Используйте аллстоп для сброса.")
            return
    except:
        pass

    chat_id = str(msg.chat.id)
    
    sessions = get_ordered_sessions()
    if not sessions:
        await msg.answer("❌ Нет доступных сессий")
        return

    sent_count = 0
    
    # Отправляем мгновенно все одновременно
    async def send_tk(username):
        nonlocal sent_count
        try:
            client = await get_or_create_client(username)
            if not client:
                return
            
            # Пишем в ЛС бота
            await client.send_message("@epidemic2_bot", "купить вакцину")
            
            # Отправляем в чат
            try:
                entity = await client.get_entity(int(chat_id))
            except:
                entity = chat_id
            
            await client.send_message(entity, "💉 Вакцина куплена")
            sent_count += 1
            logger.info(f"✅ {username} купил вакцину")
            
        except Exception as e:
            logger.error(f"❌ Ошибка {username}: {e}")

    # Мгновенно все одновременно
    await asyncio.gather(*[send_tk(username) for username in sessions])
    
    if sent_count > 0:
        await msg.answer(f"✅ Вакцина куплена {sent_count} юзерботами")
    else:
        await msg.answer("❌ Ошибка покупки вакцины")

# ===== Запись жертв через Aiogram =====
@router.message(F.text.contains("подверг заражению"))
async def catch_infection(msg: Message):
    """Ловит сообщения от игрового бота и записывает жертв"""
    try:
        text = msg.text
        if not text:
            return
        
        # Ищем ID атакующего
        attacker_id_match = re.search(r'user_id=(\d+)', text)
        if not attacker_id_match:
            return
        
        attacker_id = int(attacker_id_match.group(1))
        
        # Ищем жертву
        victim_match = re.search(r'патогеном\s+(.+)', text)
        if not victim_match:
            return
        
        victim_text = victim_match.group(1)
        victim_id_match = re.search(r'user_id=(\d+)', victim_text)
        victim_id = int(victim_id_match.group(1)) if victim_id_match else None
        
        # Ищем дни и опыт
        days_match = re.search(r'🤒\s+Заражение\s+на\s+(\d+)\s+дней', text)
        days = int(days_match.group(1)) if days_match else 0
        
        bio_match = re.search(r'☣️\s+\+([\d,]+)\s+био-опыта', text)
        bio_earn = int(bio_match.group(1).replace(',', '')) if bio_match else 0
        
        # Находим username атакующего по ID
        sessions = get_ordered_sessions()
        attacker_username = None
        
        for username in sessions:
            client = await get_or_create_client(username)
            if client:
                me = await client.get_me()
                if me.id == attacker_id:
                    attacker_username = username
                    break
        
        if not attacker_username:
            logger.error(f"❌ Не найден юзербот с ID {attacker_id}")
            return
        
        # Записываем в БД
        now = datetime.now()
        expire_date = now + timedelta(days=days) if days > 0 else now
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO victims (attacker_username, attacker_id, victim_id, victim_username, bio_earn, infected_date, expire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (attacker_username, attacker_id, victim_id, str(victim_id), bio_earn, now.strftime('%Y-%m-%d %H:%M:%S'), expire_date.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        logger.info(f"✅ @{attacker_username} заразил {victim_id}, +{bio_earn} опыта")
        
    except Exception as e:
        logger.error(f"Ошибка записи жертвы: {e}")

# ===== Команда /convert_corp =====
@router.message(F.text.startswith("/convert_corp"))
async def cmd_convert_corp(msg: Message, repo_biowar=None):
    if not is_admin(msg.from_user.id):
        return
    
    args = msg.text.replace("/convert_corp", "").strip()
    if not args:
        await msg.answer("❌ Использование: /convert_corp <код_корпорации>")
        return
    
    corp_code = args.split()[0]
    
    try:
        # repo_biowar должен прийти из middleware
        if not repo_biowar:
            await msg.answer("❌ repo_biowar не доступен")
            return
        
        # Получаем ID участников
        ids = await repo_biowar.get_corporation_members_ids_list(corp_code)
        
        if not ids:
            await msg.answer(f"❌ Корпорация с кодом {corp_code} не найдена")
            return
        
        # Формируем список с нумерацией и username
        result = "✅ Готовый список для аллеб:\n\n"
        
        for i, user_id in enumerate(ids, 1):
            # Пробуем получить username
            username = None
            try:
                # Ищем в сессиях
                for session_username in get_ordered_sessions():
                    client = await get_or_create_client(session_username)
                    if client:
                        me = await client.get_me()
                        if me.id == user_id:
                            username = session_username
                            break
            except:
                pass
            
            if username:
                result += f"{i}. @{username}\n"
            else:
                result += f"{i}. {user_id}\n"
        
        result += f"\nВсего: {len(ids)} целей"
        
        await msg.answer(result)
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")

# ===== Команда /convert =====
@router.message(F.text.startswith("/convert"))
async def cmd_convert(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    # Пробуем получить текст из реплая или предыдущего сообщения
    text = ""
    
    if msg.reply_to_message:
        text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
    
    # Если текст обрезан или нет реплая - берём предыдущее сообщение
    if not text or "..." in text or "1...." in text:
        try:
            # Получаем последние 5 сообщений и ищем список
            history = await msg.bot.get_messages(msg.chat.id, limit=5)
            for hist_msg in history:
                if hist_msg.text and "user_id=" in hist_msg.text:
                    text = hist_msg.text
                    print(f"DEBUG: Найден список из истории: {len(text)} символов")
                    break
        except Exception as e:
            print(f"DEBUG: Ошибка истории: {e}")
    
    # Извлекаем ID
    ids = re.findall(r'user_id=(\d+)', text)
    if not ids:
        ids = re.findall(r'\b(\d{7,})\b', text)
    
    # Убираем дубликаты
    ids = list(dict.fromkeys(ids))
    
    if not ids:
        await msg.answer("❌ Не найдены ID в сообщении")
        return
    
    # Формируем готовый список
    result = "✅ Готовый список для аллеб:\n\n"
    result += " ".join(ids)
    result += f"\n\nВсего: {len(ids)} целей"
    
    await msg.answer(result)

# ===== Команда ЧК =====
@router.message(F.text.lower().startswith("чк"))
async def cmd_chk(msg: Message):
    global INFECTION_RUNNING
    
    if not is_admin(msg.from_user.id):
        return
    
    # Проверяем флаг
    try:
        from core.userbot.userbot_manager import INFECTION_RUNNING as INF_FLAG, get_stop_flag
        if INF_FLAG:
            await msg.answer("⚠️ Заражение уже запущено! Дождитесь окончания.")
            return
        if get_stop_flag():
            await msg.answer("⏹️ Команды остановлены! Используйте аллстоп для сброса.")
            return
    except:
        pass

    chat_id = str(msg.chat.id)
    target_username = None
    target_id = None

    text_cmd = msg.text.lower().replace("чк", "").strip()

    if text_cmd.startswith('@'):
        target_username = text_cmd[1:]
    elif text_cmd.isdigit():
        target_id = int(text_cmd)
    elif 't.me/' in text_cmd:
        target_username = text_cmd.split('/')[-1]
    elif 'tg://openmessage' in text_cmd:
        id_match = re.search(r'user_id=(\d+)', text_cmd)
        if id_match:
            target_id = int(id_match.group(1))

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target_id = msg.reply_to_message.from_user.id
        target_username = msg.reply_to_message.from_user.username

    sessions = get_ordered_sessions()
    if not sessions:
        await msg.answer("❌ Нет доступных сессий")
        return

    sent_count = 0
    await asyncio.sleep(0.75)

    async def send_chk(username, target_username_param=None, target_id_param=None):
        nonlocal sent_count
        try:
            target_username = target_username_param
            target_id = target_id_param
            display_username = target_username if target_username else username

            client = await get_or_create_client(username)
            if not client:
                return

            try:
                entity = await client.get_entity(int(chat_id))
            except:
                entity = chat_id

            me = await client.get_me()
            userbot_id = me.id

            # Если указан ID - получаем username
            if target_id and not target_username:
                try:
                    target_username = await get_username_by_id(client, target_id)
                except:
                    pass

            if target_id:
                target_value = str(target_id)
            elif target_username:
                target_value = target_username
            else:
                target_value = str(userbot_id)

            # Отображаем username вместо ID
            display_username = target_username if target_username else display_username

            victims = get_victims(username)

            if victims:
                for victim in victims:
                    victim_username = victim[0]
                    bio_earn = victim[1]
                    expire_date = victim[2]
                    victim_id = victim[3]

                    text = f"🙏 {display_username} +{bio_earn:,} опыта до {expire_date}"

                    await client.send_message(entity, text)
                    
                    # Отправляем кнопки от основного бота
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="⚡ 1 раз", callback_data=f"chk_infect:{username}:{target_value}:1:{chat_id}"),
                            InlineKeyboardButton(text="💥 x10", callback_data=f"chk_infect:{username}:{target_value}:10:{chat_id}")
                        ],
                        [
                            InlineKeyboardButton(text="❌ Закрыть", callback_data="chk_close")
                        ]
                    ])
                    await msg.answer("⚡", reply_markup=kb)
                    
                    sent_count += 1
                    logger.info(f"✅ {username} отправил: {text}")
                    await asyncio.sleep(0.2)
            else:
                text = f"🙏 {display_username} — Желаете ебнуть сучку? 💦"

                await client.send_message(entity, text)
                
                # Отправляем кнопки от основного бота
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="⚡ 1 раз", callback_data=f"chk_infect:{username}:{target_value}:1:{chat_id}"),
                        InlineKeyboardButton(text="💥 x10", callback_data=f"chk_infect:{username}:{target_value}:10:{chat_id}")
                    ],
                    [
                        InlineKeyboardButton(text="❌ Закрыть", callback_data="chk_close")
                    ]
                ])
                await msg.answer("⚡", reply_markup=kb)
                
                sent_count += 1
                logger.info(f"✅ {username} отправил: {text}")

        except Exception as e:
            logger.error(f"❌ Ошибка {username}: {e}")

    # Отправляем последовательно с задержкой 0.5 сек
    for username in sessions:
        await send_chk(username, target_username, target_id)
        await asyncio.sleep(0.5)

    # Тихий режим - без итогового сообщения
    pass

# ===== Обработчик callback для юзерботов =====
async def setup_userbot_callbacks(client, my_username):
    @client.on(events.CallbackQuery())
    async def callback_handler(event):
        try:
            data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
            logger.info(f"🔘 {my_username} получил callback: {data}")

            if data == "chk_close":
                await event.delete()
                await event.answer("❌ Закрыто")
                return

            if data.startswith("chk_infect:"):
                parts = data.split(":")
                target_value = parts[1]
                count = int(parts[2])

                if target_value.isdigit():
                    target_text = f"tg://openmessage?user_id={target_value}"
                else:
                    target_text = f"@{target_value}"

                if count == 1:
                    command_text = f"заразить {target_text}"
                else:
                    command_text = f"заразить {count} {target_text}"

                await client.send_message(event.chat_id, command_text)
                await event.answer(f"✅ Отправлено x{count}")
                logger.info(f"✅ {my_username} отправил: {command_text}")

        except Exception as e:
            logger.error(f"Ошибка callback {my_username}: {e}")

# ===== Callback для кнопок основного бота =====
@router.callback_query(F.data.startswith("chk_infect:"))
async def chk_infect(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("❌ Нет доступа", show_alert=True)

    parts = call.data.split(":")
    username = parts[1]
    target_value = parts[2]
    count = int(parts[3])
    chat_id_str = parts[4]

    if target_value.isdigit():
        target_text = f"tg://openmessage?user_id={target_value}"
    else:
        target_text = f"@{target_value}"

    if count == 1:
        command_text = f"заразить {target_text}"
    else:
        command_text = f"заразить {count} {target_text}"

    success = False
    try:
        client = await get_or_create_client(username)
        if client:
            try:
                chat_id_int = int(chat_id_str)
                entity = await client.get_entity(chat_id_int)
            except:
                entity = chat_id_str
            await client.send_message(entity, command_text)
            success = True
            logger.info(f"✅ {username} отправил в {chat_id_str}: {command_text}")
    except Exception as e:
        logger.error(f"❌ Ошибка {username}: {e}")

    await call.answer(f"✅ {username} отправил x{count}!" if success else "❌ Ошибка отправки")

@router.callback_query(F.data == "chk_close")
async def chk_close(call: CallbackQuery):
    await call.message.delete()
    await call.answer()

# ===== Слушатель заражений =====
# ===== Заглушка (слушатель перенесён в Aiogram) =====
async def start_victim_listener():
    pass

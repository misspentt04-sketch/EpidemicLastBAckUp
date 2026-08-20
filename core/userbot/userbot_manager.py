import asyncio
import logging
import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from telethon import TelegramClient
from telethon.sessions import StringSession

from .session_manager import (
    get_all_sessions,
    delete_session,
    disconnect_all_clients,
    init_sessions_dir,
    load_telethon_session
)

logger = logging.getLogger(__name__)

router = Router()

ADMIN_IDS = [1758346431, 7972320837]

API_ID = 29154972
API_HASH = "cc13cd6917234b587cf47048ba69072d"

init_sessions_dir()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("register"))
async def cmd_register(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Доступ запрещен")
        return

    text = """РУЧНАЯ РЕГИСТРАЦИЯ

Скопируйте и вставьте в панель сервера:

cat > create_session.py << 'EOF'
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from pathlib import Path

API_ID = 29154972
API_HASH = "cc13cd6917234b587cf47048ba69072d"

async def main():
    phone = input("Номер (+380...): ").strip()
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start(phone=phone)
    me = await client.get_me()
    username = me.username or f"id_{me.id}"
    session_string = client.session.save()
    await client.disconnect()
    sessions_dir = Path("data/sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    file_path = sessions_dir / f"{username}.session"
    with open(file_path, "w") as f:
        f.write(session_string)
    print(f"OK: @{username}")

if __name__ == "__main__":
    asyncio.run(main())
EOF

python3 create_session.py"""
    
    await msg.answer(text)

@router.message(Command("sessions"))
async def cmd_sessions(msg: Message):
    if not is_admin(msg.from_user.id):
        return

    try:
        sessions = get_all_sessions()
        if not sessions:
            await msg.answer("📭 Сессий пока нет.")
            return

        text = "📋 Сохраненные сессии:\n\n"
        for i, username in enumerate(sessions, 1):
            text += f"{i}. @{username}\n"
        
        text += f"\nВсего: {len(sessions)} сессий"
        text += "\n\nДля удаления: /del @username"
        
        await msg.answer(text)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await msg.answer(f"❌ Ошибка: {str(e)}")

@router.message(Command("del"))
async def cmd_delete_session(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Доступ запрещен")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("❌ Использование: /del @username")
        return
    
    username = args[1].replace('@', '')
    
    if delete_session(username):
        await msg.answer(f"✅ Сессия @{username} удалена!")
    else:
        await msg.answer(f"❌ Сессия @{username} не найдена")

@router.message(Command("disconnect"))
async def cmd_disconnect(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("⛔ Доступ запрещен")
        return
    
    await disconnect_all_clients()
    await msg.answer("✅ Все юзерботы отключены!")

@router.message(F.text.lower().startswith("аллеб"))
async def cmd_alleb(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    chat_id = str(msg.chat.id)
    full_text = msg.text.lower().replace("аллеб", "").strip()
    reply_to_id = msg.reply_to_message.message_id if msg.reply_to_message else None
    
    target_ids = []
    
    # Если есть реплай
    if reply_to_id and msg.reply_to_message and msg.reply_to_message.text:
        reply_text = msg.reply_to_message.text
        # Ищем все ID и username в тексте
        ids = re.findall(r'\b(\d{7,})\b', reply_text)
        usernames = re.findall(r'@([a-zA-Z0-9_]+)', reply_text)
        all_targets = ids + usernames
        
        # Парсим диапазон
        if full_text and '-' in full_text:
            try:
                parts = full_text.split('-')
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                if start <= len(all_targets) and end <= len(all_targets):
                    target_ids = all_targets[start-1:end]
                else:
                    await msg.answer(f"❌ Неверный диапазон! Доступно: 1-{len(all_targets)}")
                    return
            except:
                await msg.answer("❌ Неверный формат! Пример: аллеб 1-3")
                return
        elif full_text and full_text.isdigit():
            idx = int(full_text) - 1
            if idx < len(all_targets):
                target_ids = [all_targets[idx]]
            else:
                await msg.answer(f"❌ Номер {full_text} не найден! Доступно: 1-{len(all_targets)}")
                return
        else:
            # Берем все цели
            target_ids = all_targets
        
        if not target_ids:
            await msg.answer("❌ Не найдены ID или @username в реплае!")
            return
    else:
        # Нет реплая - обычная логика
        if full_text:
            words = full_text.split()
            target = None
            arg = None
            first_word = words[0] if words else ""
            
            if first_word.startswith('tg://openmessage'):
                target = first_word
                if len(words) > 1:
                    arg = " ".join(words[1:])
            elif first_word.startswith('@') or first_word.isdigit() or 't.me/' in first_word:
                target = first_word
                if len(words) > 1:
                    arg = " ".join(words[1:])
            
            if target:
                text = f"заразить {target}"
                if arg:
                    text += f" {arg}"
            else:
                text = full_text
        else:
            text = "заразить"
        
        sessions = get_all_sessions()
        if not sessions:
            await msg.answer("❌ Нет доступных сессий")
            return
        
        results = []
        delay = 0.75
        
        for i, username in enumerate(sessions):
            try:
                session_string = await load_telethon_session(username)
                if not session_string:
                    results.append(f"❌ @{username}: сессия не найдена")
                    continue
                
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                await client.connect()
                
                try:
                    await client.send_message(entity="@epidemic2_bot", message="!купить вакцину")
                except:
                    pass
                
                target_chat = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
                if reply_to_id:
                    await client.send_message(entity=target_chat, message=text, reply_to=reply_to_id)
                else:
                    await client.send_message(entity=target_chat, message=text)
                
                await client.disconnect()
                results.append(f"✅ @{username}")
                
            except Exception as e:
                logger.error(f"Ошибка {username}: {e}")
                results.append(f"❌ @{username}: {str(e)}")
            
            if i < len(sessions) - 1:
                await asyncio.sleep(delay)
        
        response = "✅ Отправлено!\n"
        response += f"📝 Текст: {text}\n"
        response += f"📊 Аккаунтов: {len(sessions)}\n\n"
        response += "\n".join(results)
        await msg.answer(response)
        return
    
    # Обработка списка жертв
    if not target_ids:
        await msg.answer("❌ Нет целей для заражения!")
        return
    
    sessions = get_all_sessions()
    if not sessions:
        await msg.answer("❌ Нет доступных сессий")
        return
    
    all_results = []
    delay = 0.75
    
    for target_idx, target in enumerate(target_ids):
        target_text = f"заразить @{target}"
        results = []
        
        for i, username in enumerate(sessions):
            try:
                session_string = await load_telethon_session(username)
                if not session_string:
                    results.append(f"❌ @{username}: сессия не найдена")
                    continue
                
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                await client.connect()
                
                try:
                    await client.send_message(entity="@epidemic2_bot", message="!купить вакцину")
                except:
                    pass
                
                target_chat = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
                # Отправляем без реплая, но с @ перед цифрами
                await client.send_message(entity=target_chat, message=target_text)
                
                await client.disconnect()
                results.append(f"✅ @{username}")
                
            except Exception as e:
                logger.error(f"Ошибка {username}: {e}")
                results.append(f"❌ @{username}: {str(e)}")
            
            if i < len(sessions) - 1:
                await asyncio.sleep(delay)
        
        all_results.append({
            'target': target,
            'text': target_text,
            'results': results
        })
        
        if target_idx < len(target_ids) - 1:
            await asyncio.sleep(0.5)
    
    response = "✅ Отправлено!\n\n"
    for item in all_results:
        response += f"🎯 {item['target']}: {item['text']}\n"
        for r in item['results']:
            response += f"  {r}\n"
        response += "\n"
    
    await msg.answer(response)

@router.message(F.text.lower().startswith("аллхил"))
async def cmd_allhil(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    chat_id = str(msg.chat.id)
    reply_to_id = msg.reply_to_message.message_id if msg.reply_to_message else None
    
    sessions = get_all_sessions()
    if not sessions:
        await msg.answer("❌ Нет доступных сессий")
        return
    
    results = []
    delay = 0.75
    text = "💊 Хил"
    
    for i, username in enumerate(sessions):
        try:
            session_string = await load_telethon_session(username)
            if not session_string:
                results.append(f"❌ @{username}: сессия не найдена")
                continue
            
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            
            try:
                await client.send_message(entity="@epidemic2_bot", message="!купить вакцину")
                logger.info(f"[{username}] Отправлена команда !купить вакцину")
            except Exception as e:
                logger.error(f"[{username}] Ошибка отправки вакцины: {e}")
            
            target = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
            if reply_to_id:
                await client.send_message(entity=target, message=text, reply_to=reply_to_id)
            else:
                await client.send_message(entity=target, message=text)
            
            await client.disconnect()
            results.append(f"✅ @{username}")
            
        except Exception as e:
            logger.error(f"Ошибка {username}: {e}")
            results.append(f"❌ @{username}: {str(e)}")
        
        if i < len(sessions) - 1:
            await asyncio.sleep(delay)
    
    response = "💊 Хил отправлен!\n"
    response += f"📝 Текст: {text}\n"
    response += f"📊 Аккаунтов: {len(sessions)}\n\n"
    response += "\n".join(results)
    await msg.answer(response)

@router.message(Command("reghelp"))
async def cmd_reghelp(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    await msg.answer(
        "УПРАВЛЕНИЕ ЮЗЕРБОТАМИ\n\n"
        "/register - Инструкция по ручной регистрации\n"
        "/sessions - Список всех сессий\n"
        "/del @username - Удалить сессию\n"
        "/disconnect - Отключить всех юзерботов\n\n"
        "аллеб - отправить 'заразить' в текущий чат\n"
        "аллеб текст - отправить текст в текущий чат\n"
        "аллеб 1-3 (реплай) - заразить список из реплая\n"
        "аллхил - 💊 Хил + !купить вакцину\n"
        "аллеб (реплай) - ответить на сообщение\n\n"
        "Задержка между аккаунтами: 750 мс"
    )

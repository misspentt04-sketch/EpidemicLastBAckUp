import asyncio
import logging
import re
import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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

# ===== ПОРЯДОК АККАУНТОВ =====
ORDER_FILE = "data/sessions_order.json"

def load_order():
    try:
        if os.path.exists(ORDER_FILE):
            with open(ORDER_FILE, 'r') as f:
                return json.load(f)
        return []
    except:
        return []

def save_order(order):
    try:
        os.makedirs("data", exist_ok=True)
        with open(ORDER_FILE, 'w') as f:
            json.dump(order, f, indent=2)
    except:
        pass

def get_ordered_sessions():
    all_sessions = get_all_sessions()
    order = load_order()
    if order:
        ordered = [s for s in order if s in all_sessions]
        for s in all_sessions:
            if s not in ordered:
                ordered.append(s)
        return ordered
    return all_sessions



# Флаг остановки
STOP_SPAM = False

def set_stop_flag(value: bool):
    global STOP_SPAM
    STOP_SPAM = value

def get_stop_flag() -> bool:
    return STOP_SPAM

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

@router.message(Command("order"))
async def cmd_order(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    sessions = get_ordered_sessions()
    if not sessions:
        await msg.answer("📭 Нет сессий")
        return
    
    text = "📋 **ПОРЯДОК АККАУНТОВ**\n\n"
    for i, s in enumerate(sessions, 1):
        text += f"{i}. @{s}\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for i, s in enumerate(sessions):
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=f"{i+1}. @{s}", callback_data="noop"),
            InlineKeyboardButton(text="⬆️", callback_data=f"ord_up:{s}"),
            InlineKeyboardButton(text="⬇️", callback_data=f"ord_down:{s}")
        ])
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="🔄 Сбросить", callback_data="ord_reset")
    ])
    
    await msg.answer(text, reply_markup=kb)

@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()

@router.callback_query(F.data.startswith("ord_up:"))
async def order_up(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("❌ Нет доступа", show_alert=True)
    
    s = call.data.split(":")[1]
    order = load_order()
    all_s = get_all_sessions()
    
    if not order:
        order = all_s.copy()
    
    if s not in order:
        order.insert(0, s)
    else:
        idx = order.index(s)
        if idx > 0:
            order[idx], order[idx-1] = order[idx-1], order[idx]
    
    save_order(order)
    await call.answer(f"✅ @{s} поднят")
    await cmd_order(call.message)

@router.callback_query(F.data.startswith("ord_down:"))
async def order_down(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("❌ Нет доступа", show_alert=True)
    
    s = call.data.split(":")[1]
    order = load_order()
    all_s = get_all_sessions()
    
    if not order:
        order = all_s.copy()
    
    if s not in order:
        order.append(s)
    else:
        idx = order.index(s)
        if idx < len(order) - 1:
            order[idx], order[idx+1] = order[idx+1], order[idx]
    
    save_order(order)
    await call.answer(f"✅ @{s} опущен")
    await cmd_order(call.message)

@router.callback_query(F.data == "ord_reset")
async def order_reset(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("❌ Нет доступа", show_alert=True)
    
    save_order([])
    await call.answer("🔄 Порядок сброшен")
    await cmd_order(call.message)



@router.message(F.text.lower().startswith("аллстоп"))
async def cmd_stop(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    set_stop_flag(True)
    await msg.answer("⏹️ Заражение остановлено!")

@router.message(F.text.lower().startswith("аллеб"))
async def cmd_alleb(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    chat_id = str(msg.chat.id)
    full_text = msg.text.lower().replace("аллеб", "").strip()
    reply_to_id = msg.reply_to_message.message_id if msg.reply_to_message else None
    
    target_ids = []
    if reply_to_id and msg.reply_to_message and msg.reply_to_message.text:
        reply_text = msg.reply_to_message.text
        ids = re.findall(r'\b(\d{7,})\b', reply_text)
        usernames = re.findall(r'@([a-zA-Z0-9_]+)', reply_text)
        all_targets = ids + usernames
        
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
            target_ids = all_targets
        
        if not target_ids:
            await msg.answer("❌ Не найдены ID или @username в реплае!")
            return
    else:
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
        
        sessions = get_ordered_sessions()
        if not sessions:
            await msg.answer("❌ Нет доступных сессий")
            return
        
        results = []
        delay = 0.75
        
        for username in sessions:
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
                
                # Проверяем флаг перед отправкой
                if get_stop_flag():
                    await client.disconnect()
                    await msg.answer("⏹️ Заражение остановлено!")
                    set_stop_flag(False)
                    return
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
            
            # Точная задержка с учетом времени отправки
            import time
            send_start = time.time()
            elapsed = time.time() - send_start
            sleep_time = max(0, delay - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        response = "✅ Отправлено!\n"
        response += f"📝 Текст: {text}\n"
        response += f"📊 Аккаунтов: {len(sessions)}\n\n"
        response += "\n".join(results)
        await msg.answer(response)
        return
    
    if not target_ids:
        await msg.answer("❌ Нет целей для заражения!")
        return
    
    sessions = get_ordered_sessions()
    if not sessions:
        await msg.answer("❌ Нет доступных сессий")
        return
    
    all_results = []
    msg_delay = 0.75
    
    for username in sessions:
        results = []
        session_string = await load_telethon_session(username)
        if not session_string:
            results.append(f"❌ @{username}: сессия не найдена")
            all_results.append({'username': username, 'results': results})
            continue
        
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        
        try:
            await client.send_message(entity="@epidemic2_bot", message="!купить вакцину")
        except:
            pass
        
        target_chat = int(chat_id) if chat_id.lstrip('-').isdigit() else chat_id
        
        import time
        for target_idx, target in enumerate(target_ids):
            # Проверяем флаг перед каждым сообщением
            if get_stop_flag():
                await client.disconnect()
                await msg.answer("⏹️ Заражение остановлено!")
                set_stop_flag(False)
                return
            target_text = f"заразить @{target}"
            send_start = time.time()
            
            try:
                await client.send_message(entity=target_chat, message=target_text)
                results.append(f"✅ @{username} -> {target_text}")
            except Exception as e:
                results.append(f"❌ @{username} -> {target}: {str(e)}")
            
            if target_idx < len(target_ids) - 1:
                elapsed = time.time() - send_start
                sleep_time = max(0, msg_delay - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
        
        await client.disconnect()
        all_results.append({'username': username, 'results': results})
        
        if username != sessions[-1]:
            await asyncio.sleep(0.5)
    
    response = "✅ Отправлено!\n\n"
    for item in all_results:
        response += f"👤 @{item['username']}:\n"
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
    
    sessions = get_ordered_sessions()
    if not sessions:
        await msg.answer("❌ Нет доступных сессий")
        return
    
    results = []
    delay = 0.75
    text = "💊 Хил"
    
    for username in sessions:
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
        "/disconnect - Отключить всех юзерботов\n"
        "/order - Порядок аккаунтов\n\n"
        "аллеб - отправить 'заразить' в текущий чат\n"
        "аллеб 1-3 (реплай) - заразить список из реплая\n"
        "аллхил - 💊 Хил + !купить вакцину\n\n"
        "Задержка между аккаунтами: 750 мс"
    )

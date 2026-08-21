import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from pathlib import Path

API_ID = 29154972
API_HASH = "cc13cd6917234b587cf47048ba69072d"

async def rename_sessions():
    sessions_dir = Path("data/sessions")
    if not sessions_dir.exists():
        print("❌ Папка sessions не найдена")
        return
    
    for file_path in sessions_dir.glob("*.session"):
        try:
            # Читаем сессию
            with open(file_path, 'r') as f:
                session_string = f.read()
            
            # Создаем клиент для проверки
            client = TelegramClient(
                StringSession(session_string),
                API_ID,
                API_HASH
            )
            await client.connect()
            
            # Получаем информацию об аккаунте
            me = await client.get_me()
            username = me.username or f"id_{me.id}"
            
            await client.disconnect()
            
            # Переименовываем файл
            new_name = sessions_dir / f"{username}.session"
            if file_path.name != new_name.name:
                # Если файл с таким именем уже есть - удаляем
                if new_name.exists():
                    new_name.unlink()
                file_path.rename(new_name)
                print(f"✅ {file_path.name} -> {username}.session")
            
        except Exception as e:
            print(f"❌ Ошибка {file_path.name}: {e}")

if __name__ == "__main__":
    asyncio.run(rename_sessions())

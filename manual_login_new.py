import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import os
from pathlib import Path

API_ID = 29154972
API_HASH = "cc13cd6917234b587cf47048ba69072d"

async def main():
    print("=" * 50)
    print("🔐 СОЗДАНИЕ НОВОЙ СЕССИИ")
    print("=" * 50)
    
    phone = input("📱 Номер телефона (+380...): ").strip()
    
    # Создаем клиент со строковой сессией
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start(phone=phone)
    
    me = await client.get_me()
    username = me.username or f"id_{me.id}"
    
    # Сохраняем сессию как строку
    session_string = client.session.save()
    
    # Сохраняем в файл
    sessions_dir = Path("data/sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    file_path = sessions_dir / f"{username}.session"
    with open(file_path, 'w') as f:
        f.write(session_string)
    
    print("\n" + "=" * 50)
    print(f"✅ УСПЕШНО!")
    print(f"👤 Аккаунт: @{username}")
    print(f"💾 Сессия сохранена: {file_path}")
    print("=" * 50)
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

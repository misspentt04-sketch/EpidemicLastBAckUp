import asyncio
from pyrogram import Client
import os

API_ID = 29154972
API_HASH = "cc13cd6917234b587cf47048ba69072d"

async def manual_login():
    print("=" * 50)
    print("🔐 РУЧНОЙ ВХОД В АККАУНТ")
    print("=" * 50)
    
    phone = input("📱 Номер телефона (+380...): ").strip()
    
    client = Client(
        name="temp_session",
        api_id=API_ID,
        api_hash=API_HASH,
        device_model="Desktop",
        system_version="Linux",
        app_version="4.9.0"
    )
    
    await client.connect()
    print("✅ Подключено к серверу Telegram")
    
    try:
        # Пробуем отправить код
        sent_code = await client.send_code(phone)
        print(f"📩 Код отправлен! Тип: {sent_code.type}")
        print("   - APP = в Telegram")
        print("   - SMS = по SMS")
        print("   - CALL = по звонку")
        
        code = input("🔑 Введите код: ").strip()
        
        # Вход
        await client.sign_in(phone, sent_code.phone_code_hash, code)
        
        # Получаем данные
        me = await client.get_me()
        username = me.username or f"id_{me.id}"
        
        # Экспортируем сессию
        session_string = await client.export_session_string()
        
        # Сохраняем
        os.makedirs("data/sessions", exist_ok=True)
        file_path = f"data/sessions/{username}.session"
        with open(file_path, 'w') as f:
            f.write(session_string)
        
        print("\n" + "=" * 50)
        print("✅ УСПЕШНЫЙ ВХОД!")
        print(f"👤 Аккаунт: @{username}")
        print(f"🆔 ID: {me.id}")
        print(f"📱 Телефон: {me.phone_number}")
        print(f"💾 Сессия сохранена: {file_path}")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(manual_login())

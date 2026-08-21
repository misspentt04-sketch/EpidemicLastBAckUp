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

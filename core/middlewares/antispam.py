import time
from collections import defaultdict
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message

user_timestamps = defaultdict(list)
banned_users = {}

MAX_MESSAGES = 8
TIME_WINDOW = 1.0
BAN_TIME = 86400  # 24 часа
ADMIN_CHAT_ID = -1003688648228

class AntiSpamMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        if not isinstance(event, Message) or not event.from_user or event.chat.type != "private":
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()

        if user_id in banned_users:
            if now < banned_users[user_id]:
                return
            else:
                del banned_users[user_id]

        user_timestamps[user_id] = [ts for ts in user_timestamps[user_id] if now - ts < TIME_WINDOW]
        user_timestamps[user_id].append(now)

        if len(user_timestamps[user_id]) >= MAX_MESSAGES:
            banned_users[user_id] = now + BAN_TIME
            user_timestamps[user_id].clear()
            
            user = event.from_user
            bot: Bot = data.get("bot")

            try:
                msg_text = "⚠️ <b>Обнаружен спам!</b> Вы заблокированы в боте на 1 день.\nЕсли произошла ошибка, пишите @M_thousand_m"
                await event.reply(msg_text)
            except Exception:
                pass

            if bot:
                try:
                    username_str = f"@{user.username}" if user.username else "нет_юзернейма"
                    admin_log = (
                        f"🚫 <b>[Автобан AntiSpam]</b>\n"
                        f"Пользователь: <a href=\"tg://user?id={user.id}\">{user.full_name}</a> "
                        f"(<code>{user.id}</code>, {username_str})\n"
                        f"Причина: Спам (>8 сообщ/сек в ЛС)\n"
                        f"Блокировка: <b>24 часа</b>"
                    )
                    await bot.send_message(ADMIN_CHAT_ID, admin_log)
                except Exception as e:
                    print(f"[AntiSpam Log Error] {e}")

            return

        return await handler(event, data)

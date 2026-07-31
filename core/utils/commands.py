import logging
from aiogram import Bot
from aiogram.types import BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError

logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    try:
        # Здесь настраиваются команды, если они используются
        pass
    except Exception as e:
        logger.error(f"Ошибка при установке команд: {e}")

async def del_commands(bot: Bot):
    try:
        await bot.delete_my_commands(scope=BotCommandScopeAllGroupChats())
        await bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    except TelegramRetryAfter as e:
        logger.warning(f"⚠️ Telegram Flood Control на удаление команд: ждем {e.retry_after} сек. Пропускаем...")
    except TelegramAPIError as e:
        logger.error(f"⚠️ Ошибка Telegram API при удалении команд: {e}")
    except Exception as e:
        logger.error(f"⚠️ Неизвестная ошибка при удалении команд: {e}")

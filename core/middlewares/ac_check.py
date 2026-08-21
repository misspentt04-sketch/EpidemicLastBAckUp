import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from core.utils.db_api.repo_biowar import RequestsRepoBiowar

logger = logging.getLogger(__name__)

class ACMiddleware(BaseMiddleware):
    """Middleware для проверки АС (мута команд)"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        # Проверяем есть ли у пользователя АС
        repo_biowar = data.get('repo_biowar')
        if not repo_biowar:
            # Если repo нет - пропускаем
            return await handler(event, data)
        
        try:
            # Проверяем АС
            game_mute = await repo_biowar.get_user_game_mute(user_id)
            if game_mute:
                # Проверяем не истекло ли время
                import time
                time_expire = game_mute.get('time_expire')
                if time_expire and int(time_expire) > int(time.time()):
                    # АС активен - игнорируем
                    reason = game_mute.get('reason', 'Не указана')
                    logger.info(f"AC active for user {user_id}: {reason}")
                    
                    # Если это сообщение - отвечаем
                    if isinstance(event, Message):
                        await event.answer(
                            f"⛔ У вас активен АС (мут команд)!\n"
                            f"Причина: {reason}\n"
                            f"Обратитесь к администратору."
                        )
                    return  # Игнорируем
        except Exception as e:
            logger.error(f"AC check error: {e}")
        
        # Если АС нет или истек - пропускаем
        return await handler(event, data)

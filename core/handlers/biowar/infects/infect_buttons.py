from aiogram import Router, F
from aiogram.types import CallbackQuery, User, Message
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.handlers.biowar.labs.lab_text_upgrade import handle_upgrade
from redis.asyncio import Redis
from asyncio import Lock

router = Router()


def _make_fake_msg(call: CallbackQuery, owner_id: int, text: str) -> Message:
    """Создаёт фейковое сообщение с from_user=owner_id и чистым текстом."""
    fake_owner = User(
        id=owner_id,
        is_bot=False,
        first_name=call.from_user.first_name or "",
        username=call.from_user.username,
    )

    # model_copy + явное обнуление всех сущностей, которые могут помешать парсингу
    fake = call.message.model_copy(update={
        'from_user': fake_owner,
        'text': text,
        'caption': None,
        'reply_to_message': None,
        'entities': None,
        'caption_entities': None,
    })

    # Явно задаём override_target_id, чтобы infect() не парсил никого другого
    return fake


@router.callback_query(F.data.startswith("repeat_infect:"))
async def repeat_infect_cb(call: CallbackQuery, bot, db: Cursor,
                           repo_biowar: RequestsRepoBiowar,
                           redis: Redis, lock: Lock):
    try:
        _, target_id, owner_id, pats = call.data.split(":")
        target_id = int(target_id)
        owner_id = int(owner_id)
        pats = int(pats)
    except Exception:
        return await call.answer("❌ Ошибка данных", show_alert=True)

    if call.from_user.id != owner_id:
        return await call.answer("❌ Это не твоя кнопка!", show_alert=True)

    from core.handlers.biowar.infects.infect import infect

    fake_message = _make_fake_msg(call, owner_id, f'заразить {target_id} {pats}')

    # Жёстко фиксируем цель через override + отдельно кладём в атрибут
    setattr(fake_message, '_override_target_id', target_id)

    await call.answer(f"🔁 Повтор: {pats} пат. → цель {target_id}")
    await infect(msg=fake_message, bot=bot, db=db, repo_biowar=repo_biowar,
                 redis=redis, lock=lock)


@router.callback_query(F.data.startswith("up_infect:"))
async def up_infect_cb(call: CallbackQuery, db: Cursor,
                       repo_biowar: RequestsRepoBiowar):
    try:
        _, owner_id, count = call.data.split(":")
        owner_id = int(owner_id)
        count = int(count)
    except Exception:
        return await call.answer("❌ Ошибка данных", show_alert=True)

    if call.from_user.id != owner_id:
        return await call.answer("❌ Это не твоя кнопка!", show_alert=True)

    fake_message = _make_fake_msg(call, owner_id, f'+зз {count}')

    await call.answer(f"🎯 Прокачка +{count} ЗЗ")
    await handle_upgrade(fake_message, db, repo_biowar, "infect")

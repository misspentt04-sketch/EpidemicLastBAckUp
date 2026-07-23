from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandObject
from aiogram import Bot

from redis import Redis
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar

from core.data.story.story import tricks_story
from core.data.tricks.tricks_chat_manage import tricks_cm

# from core.handlers.biowar.donates.donate import donate_func

from core.keyboards.inline.tutorial_begin import start_action, help_kb


async def start(msg: Message, command: CommandObject, db: Cursor, bot: Bot, redis: Redis, repo_biowar: RequestsRepoBiowar):
    
# if command.args == 'donate':
#     return await donate_func(msg, bot, db, repo_biowar, deep_link=True)
    
    await repo_biowar.add_data_tutorial(msg.from_user.id)
    picture = await redis.get('epidemic_tutorial_begin_img')
    
    tutorial = await repo_biowar.get_tutorial(msg.from_user.id)
    
    if tutorial['is_tutorial_complete'] == 0:
        if not picture:
            with open('media/tutorial_begin.jpg', 'rb') as img:
                result = await msg.answer_photo(
                    BufferedInputFile(
                        img.read(),
                        filename='tutorial_begin.jpg'
                    ),
                    caption=tricks_story['start_action'],
                    reply_markup=start_action(),
                    disable_web_page_preview=True
                )
                await redis.set('epidemic_tutorial_begin_img', result.photo[-1].file_id)
        else:
            await msg.answer_photo(
                picture,
                caption=tricks_story['start_action'],
                reply_markup=start_action(),
                disable_web_page_preview=True
            )
    else:
        
        admin_list = tricks_cm['start']['menu_admin_list']
        online = []
        offline = []
        
        for key, val in admin_list.items():
            admin = await redis.get(f'epidemic_help_admin_status:{key}')
            if admin:
                online.append(val)
            else:
                offline.append(val)
        
        text = tricks_cm['start']['menu'].format(
            '\n'.join(online),
            '\n'.join(offline)
        )
        
        await msg.answer(text, reply_markup=help_kb(), disable_web_page_preview=True)


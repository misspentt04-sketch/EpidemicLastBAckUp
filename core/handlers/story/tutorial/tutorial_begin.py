from aiogram import Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from asyncmy.cursors import Cursor
from redis.asyncio import Redis

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.callbackdata import Tutorial

from core.data.tricks.tricks_chat_manage import tricks_cm
from core.data.tricks.tricks_biowar import tricks_biowar
from core.data.tricks.stickers import stickers
from core.data.story.story import tricks_story

from core.keyboards.inline.tutorial_begin import (
    start_action, tutorial_continue,
    tutorial_2_kb, tutorial_3_kb, tutorial_4_kb,
    tutorial_5_kb, tutorial_6_kb
)

from core import func


import asyncio

# async def tutorial_start_action(
#     call: CallbackQuery,
#     bot: Bot,
#     callback_data: TutorialStartAction,
#     db: Cursor,
#     redis: Redis,
#     repo_biowar: RequestsRepoBiowar):
    
#     id = call.from_user.id
    
#     text = tricks_story['start_action'] + '\n' + tricks_story['give_starter_pet']
    
#     pets = await repo_biowar.get_my_pets(id)

#     if not pets or not any([p for p in pets if p['pet_name'].lower() == 'первопроходец']):
#         await repo_biowar.give_pet(id, 'первопроходец', 'гармония')
#         await repo_biowar.change_current_pet(id, 'первопроходец')
#         await redis.hset(id, mapping={'pet_vuln_indicator': 100})
#         await call.message.answer(text)
#         await call.message.answer_sticker(stickers['pet']['первопроходец'])
#         await asyncio.sleep(1)
#         # pet_info = tricks_biowar['pet']['pets_info']['первопроходец']
#         # await call.message.answer(tricks_biowar['pet']['get_my_pet'].format(
#         #     pet_info['emoji'], 'первопроходец'.title(), pet_info['element_emoji'],
#         #     pet_info['element'], '<i>' + pet_info['skill'] + '</i>'
#         # ))
#         await call.answer()
#     else:
#         await call.message.answer(tricks_cm['start']['menu'], disable_web_page_preview=True)
#         return await call.answer()
    

async def tutorial_1_continue(call: CallbackQuery, callback_data: Tutorial):
    
    text = tricks_story['tutorial_continue']
    
    await call.message.delete()
    await call.message.answer(text, reply_markup=tutorial_continue(), disable_web_page_preview=True)
    await call.answer()

async def tutorial_1_discontinue(call: CallbackQuery, callback_data: Tutorial, repo_biowar: RequestsRepoBiowar):
    
    text = tricks_story['tutorial_discontinue']
    
    await repo_biowar.update_is_tutorial_complete(call.from_user.id, 1)
    
    await call.message.delete()
    await call.message.answer(text, disable_web_page_preview=True)
    await call.answer()

async def restart_tutorial(msg: Message, repo_biowar: RequestsRepoBiowar):
    
    await repo_biowar.update_is_tutorial_complete(msg.from_user.id, 0)
    
    await msg.answer(tricks_story['start_action'], reply_markup=start_action(), disable_web_page_preview=True)

async def tutorial_2(call: CallbackQuery, callback_data: Tutorial):
    
    text = tricks_story['tutorial_2']
    
    await call.message.delete()
    await call.message.answer(text, reply_markup=tutorial_2_kb(), disable_web_page_preview=True)
    await call.answer()

async def tutorial_3(call: CallbackQuery, callback_data: Tutorial):
    
    text = tricks_story['tutorial_3']
    
    await call.message.delete()
    await call.message.answer(text, reply_markup=tutorial_3_kb(), disable_web_page_preview=True)
    await call.answer()

async def tutorial_4(call: CallbackQuery, callback_data: Tutorial):
    
    text = tricks_story['tutorial_4']
    
    await call.message.delete()
    await call.message.answer(text, reply_markup=tutorial_4_kb(), disable_web_page_preview=True)
    await call.answer()

async def tutorial_5(call: CallbackQuery, callback_data: Tutorial):
    
    text = tricks_story['tutorial_5']
    
    await call.message.delete()
    await call.message.answer(text, reply_markup=tutorial_5_kb(), disable_web_page_preview=True)
    await call.answer()

async def tutorial_6(call: CallbackQuery, callback_data: Tutorial):
    
    text = tricks_story['tutorial_6']
    
    await call.message.delete()
    await call.message.answer(text, reply_markup=tutorial_6_kb(), disable_web_page_preview=True)
    await call.answer()

async def tutorial_7(call: CallbackQuery, callback_data: Tutorial, redis: Redis, repo_biowar: RequestsRepoBiowar):
    
    text = tricks_story['tutorial_7']
    user_id = call.from_user.id
    
    picture = await redis.get('epidemic_tutorial_end_img')
    gif = await redis.get('epidemic_tutorial_end_gif')
    await repo_biowar.update_is_tutorial_complete(call.from_user.id, 1)
    
    text_gif = '❄️ <b>Великодушная и элегантная учёная</b>, член Общества гениев №81, эксперт в области биологических наук. Это я - <b>Жуань Мэй</b>.\n\n<blockquote>Отправляю тебя в длинное путешествие даря тебе питомца Первопроходца, а пока-что прощай. Возможно мы увидимся <u>не один раз</u> на протяжении твоего пути.</blockquote>'
    
    pets = await repo_biowar.get_my_pets(user_id)

    if not pets or not any([p for p in pets if p['pet_name'].lower() == 'первопроходец']):
        await repo_biowar.give_pet(user_id, 'первопроходец', 'гармония')
        await repo_biowar.change_current_pet(user_id, 'первопроходец')
        await redis.hset(user_id, mapping={'pet_vuln_indicator': 100})
    
    await call.message.delete()
    
    if not picture:
        with open('media/tutorial_end.jpg', 'rb') as img:
            result = await call.message.answer_photo(
                BufferedInputFile(
                    img.read(),
                    filename='tutorial_end.jpg'
                ),
                caption=text,
                disable_web_page_preview=True
            )
            await redis.set('epidemic_tutorial_end_img', result.photo[-1].file_id)
    else:
        await call.message.answer_photo(
            picture,
            caption=text,
            disable_web_page_preview=True
        )
    await asyncio.sleep(3)
    if not gif:
        with open('media/tutorial_end_ruan_mei.mp4', 'rb') as gif:
            result = await call.message.answer_animation(
                BufferedInputFile(
                    gif.read(),
                    filename='tutorial_end_ruan_mei.mp4'
                ),
                caption=text_gif
            )
            await redis.set('epidemic_tutorial_end_gif', result.animation.file_id)
    else:
        await call.message.answer_animation(gif, caption=text_gif)
    
    await call.answer()
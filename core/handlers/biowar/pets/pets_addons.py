from aiogram.types import Message, BufferedInputFile
from asyncmy.cursors import Cursor
from aiogram import Bot

from redis import Redis

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core.data.tricks.tricks_biowar import tricks_biowar
from core.data.tricks.tricks_genai import tricks_genai
from core.data.icons import LabIco, OtherIco, PetIco
from core.data.tricks.stickers import stickers
# from core.utils.silero_tts import silero
from core.utils.genai import gpt_thinks

from core import func
from core.settings import settings

from humanize import intcomma
from datetime import datetime, timedelta

import random


async def pet_the_pet(msg: Message, bot: Bot, redis: Redis, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    pet = await repo_biowar.get_my_pet(id)
    pet_owner_id = await redis.get(f'epidemic_pet_owner_msg:{msg.chat.id}:{msg.reply_to_message.message_id}')
    bag = await repo_biowar.get_bag(id)
    pet_is_owner = pet_owner_id and id == int(pet_owner_id)
    
    # errors
    if not pet and pet_is_owner:
        return await msg.answer(tricks_biowar['pet']['hasnt_pet'], disable_web_page_preview=True)
    if msg.reply_to_message.from_user.id != settings.bots.bot_id:
        return
    
    if not pet_is_owner:
        pet_stranger = await repo_biowar.get_my_pet(pet_owner_id)
        primogems_stole = random.randint(1, 15)
        primogems_stole = (
            bag['primogem'] - primogems_stole + \
            bag['primogem'] + primogems_stole \
                if bag['primogem']-primogems_stole < 0
                else
            primogems_stole
        )
        await repo_biowar.update_bag_primogem(id, primogem=primogems_stole, operator='-')
        if primogems_stole != 0:
            text = gpt_thinks(tricks_genai['prompts']['pets'][pet_stranger['current_pet']]['pet_the_pet_stranger'])
        else:
            text = gpt_thinks(tricks_genai['prompts']['pets']['zero_primogem'])
        return await msg.answer(text)
    exempt_pet_ids = {
        int(admin_id)
        for admin_id in settings.bots.admin_id
        if str(admin_id).lstrip('-').isdigit()
    }

    if (
        id not in exempt_pet_ids and
        pet['pet_the_pet_time'] != 0 and pet['pet_the_pet_time'] > datetime.utcnow().timestamp()
    ):
        next_pet_the_pet_time = func.diff_convert_timestamp_to_human(pet['pet_the_pet_time'])
        return await msg.answer(tricks_biowar['pet']['not_pet_the_pet_time'].format(next_pet_the_pet_time))
    
    lab = await repo_biowar.get_info_user_lab(id)

    rand_val = [1, 70]
    pet_boost_exp = ''

    if pet['current_pet'].lower() == 'аквелиа':
        rand_val = [1, 120]
    if pet['current_pet'].lower() == 'первопроходец':
        pet_boost_exp = lab['pet_boost_exp'] if lab['pet_boost_exp'] != 0 else 0
        pet_boost_exp = f'<i>Бонус от способности пета принес вам <b>+{pet_boost_exp}</b> 🧬</i>'
        await repo_biowar.update_pet_boost_exp(id, 0)

    primogem_claim = random.randint(*rand_val)
    happy_current = func.adjust_value(pet['happy'], tricks_biowar['max']['pet_happy_recover_percent'], '+')
    
    pet_the_pet_text = gpt_thinks(
        tricks_genai['prompts']['pets'][pet['current_pet']]['pet_the_pet'].format(pet['happy'])
        ).replace('\n', '')
    
    text = tricks_biowar['pet']['pet_the_pet'].format(
        pet_the_pet_text,
        primogem_claim,
        happy_current,
        pet_boost_exp
    )

    pet_the_pet_time = (datetime.utcnow() + timedelta(hours=12)).timestamp()
    
    await repo_biowar.update_bag_primogem(id, primogem_claim)
    await repo_biowar.setup_pet_the_pet(id, pet_the_pet_time, happy_current)
    
    # if random.randint(1, 2) == 1:
    #     await bot.send_chat_action(msg.chat.id, 'record_voice', request_timeout=15)
    #     voice = silero.generate_audio(pet_the_pet_text)
    #     await bot.send_chat_action(msg.chat.id, 'upload_voice', request_timeout=15)
    #     send_msg = await msg.answer_voice(BufferedInputFile(voice.getvalue(), 'voice.ogg'), caption=text)
    # else:
    send_msg = await msg.answer(text)
    
    await redis.set(
        f'epidemic_pet_msg:{msg.chat.id}:{send_msg.message_id}',
        f'{msg.from_user.id}:{pet['current_pet']}:pet_the_pet:{pet_the_pet_text}'
    )

async def pet_notify_reply_answ(msg: Message, bot: Bot, redis: Redis, repo_biowar: RequestsRepoBiowar):
    
    redis_key = f'epidemic_pet_msg:{msg.chat.id}:{msg.reply_to_message.message_id}'
    msg_data = await redis.get(redis_key)
    
    if not msg_data:
        return
    
    user_id = msg_data.partition(':')[0]
    pet_name = msg_data.partition(':')[-1].partition(':')[0]
    pet_msg_type = msg_data.partition(':')[-1].partition(':')[-1].partition(':')[0]
    pet_text = msg_data.partition(':')[-1].partition(':')[-1].partition(':')[-1]
    
    pet = await repo_biowar.get_my_pet(user_id)
    text_for_ai = ''
    
    if pet_msg_type == 'pet_notify':
        text_for_ai += tricks_genai['prompts']['pets'][pet['pet_name'].lower()]['pet_the_pet_notify_reply_answ'].format(
            pet_name, pet_text, msg.text
        )
    elif pet_msg_type == 'pet_the_pet':
        text_for_ai += tricks_genai['prompts']['pets'][pet['pet_name'].lower()]['pet_the_pet_answ'].format(
            pet_text, msg.text
        )
    
    ai_text = gpt_thinks(text_for_ai)
    
    await redis.delete(redis_key)
    
    # if random.randint(1, 2) == 1:
    #     await bot.send_chat_action(msg.chat.id, 'record_voice', request_timeout=15)
    #     voice = silero.generate_audio(ai_text)
    #     await bot.send_chat_action(msg.chat.id, 'upload_voice', request_timeout=15)
    #     await msg.answer_voice(BufferedInputFile(voice.getvalue(), 'voice.ogg'), caption=ai_text)
    # else:
    await msg.answer(ai_text)

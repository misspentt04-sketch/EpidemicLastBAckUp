from asyncmy.cursors import Cursor
from redis.asyncio import Redis
from aiogram.types import Message
from aiogram import Bot

from humanize import intcomma
from datetime import datetime

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core import func

from core.data.tricks.tricks_biowar import tricks_biowar

import random


async def buy_vaccine(msg: Message, bot: Bot, db: Cursor, redis: Redis, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    lab_info = await repo_biowar.get_info_user_lab(id)
    
    if not lab_info['fever']:
        return await msg.answer(tricks_biowar['infect']['have_not_fever'])
    
    pet = await repo_biowar.get_my_pet(id)
    pet_effect = ''
    
    fev_minutes = (datetime.fromtimestamp(lab_info['fever']) - datetime.utcnow()).total_seconds() / 60
    fev_minutes = 1 if fev_minutes <= 0 else fev_minutes
    fever_price = int(fev_minutes * lab_info['lethality'] / tricks_biowar['price']['multiply']['infect_fever_time'])
    fever_price = 1 if fever_price <= 0 else fever_price
    
    if pet and pet['current_pet'].lower() == 'мимин':
        fever_price_ = fever_price
        element_pet_emoji = tricks_biowar['pet']['pets_info'][pet['current_pet'].lower()]['element_emoji']
        fever_price = int(fever_price - (fever_price * tricks_biowar['pet']['pets_info'][pet['current_pet'].lower()]['skill_val']))
        pet_effect += f'<b>{element_pet_emoji} {pet["current_pet"].title()}</b> cнизил расходы вакцины на <b>{intcomma(int(fever_price_-fever_price))}</b> био-ресурсов'
    
    if lab_info['bio_resource'] < fever_price:
        return await msg.answer(tricks_biowar['text']['not_enough_resources'])
    
    text = tricks_biowar['text']['buy_vaccine'].format(intcomma(fever_price), pet_effect)

    await repo_biowar.buy_vaccine(fever_price, id)
    await redis.set(f'epidemic_pet_try_count_heal:{id}', 0)
    
    await msg.answer(text)


async def victims_list(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    victims = await repo_biowar.get_victims(id)
    victims_food = await repo_biowar.get_victims_food(id)
    infected = await repo_biowar.get_my_infected(id)
    
    victims_list = func.get_victims_list(victims)
    
    text = tricks_biowar['infect']['victims_list'].format(
        '\n'.join(victims_list[0]), infected,
        victims_list[1][0], intcomma(victims_food if victims_food else 0)
    )
    
    await msg.answer(text)

async def illnesses_list(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    illness = await repo_biowar.get_illnesses(id)
    
    illness_list = func.get_illness_list(illness)
    
    text = tricks_biowar['infect']['illnesses_list'].format('\n'.join(illness_list))
    
    await msg.answer(text)

async def add_virus_signal(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    await repo_biowar.update_virus_chat_setup(id, msg.chat.id)
    
    text = tricks_biowar['infect']['add_virus_signal']
    
    await msg.answer(text)

async def del_virus_signal(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    await repo_biowar.del_virus_chat_setup(id)
    
    text = tricks_biowar['infect']['del_virus_signal']
    
    await msg.answer(text)

async def buy_vaccine_joke(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    bag = await repo_biowar.get_bag(id)
    lab = await repo_biowar.get_info_user_lab(id)
    
    text = random.choice(tricks_biowar['infect']['buy_vaccine_joke']) + '\n\n<blockquote>'
    
    bio_resource_rand = random.randint(1, 50000)
    primogem_rand = random.randint(1, 50)
    stellar_jade_rand = random.randint(1, 15)
    
    bio_resource_cost = func.adjust_value(lab['bio_resource'], bio_resource_rand, '-', 0)
    primogem_cost = func.adjust_value(bag['primogem'], primogem_rand, '-', 0)
    stellar_jade_cost = func.adjust_value(bag['stellar_jade'], stellar_jade_rand, '-', 0)
    
    text += f'┌ 🧬 Утилизировано <b>{bio_resource_rand}</b> био-ресурсов...\n'
    if random.randint(1, 2) == 1:
        text += f'├ 💠 скурено <b>{primogem_rand}</b> примогемов...\n'
        await repo_biowar.update_bag_primogem(id, primogem_cost, None)
        if random.randint(1, 5) == 1:
            text += f'└ ✨ а ещё <b>{stellar_jade_rand}</b> нефрита...'
            await repo_biowar.update_bag_stellar_jade(id, stellar_jade_cost, None)
    
    text += '</blockquote>'
    await repo_biowar.update_lab_skill_val(id, 'bio_resource', bio_resource_cost)
    
    await msg.answer(text)


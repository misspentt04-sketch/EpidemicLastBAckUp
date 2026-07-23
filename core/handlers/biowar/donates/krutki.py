from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram import Bot

from redis import Redis

from core.keyboards.inline.pets import global_pets_list_nav
from core.utils.callbackdata import PetsGlobalListChoose
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar, Const
from core.data.tricks.stickers import stickers
from core.data.icons import BagIco
from core import func

import html
import random
import asyncio


KRUTKA_GARANT = 30

async def krutka(msg: Message, repo_biowar: RequestsRepoBiowar, redis: Redis):
    
    id = msg.from_user.id
    bag = await repo_biowar.get_bag(id)
    
    krutka_cost = 160
    
    stellar_jade = bag['stellar_jade']
    user = await repo_biowar.get_user(id)
    link = func.ping_link(id, user['full_name'])
    krutka_garant = await repo_biowar.get_krutka_garant(id)
    
    # errors
    if krutka_cost > stellar_jade:
        return msg.reply(tricks_biowar['bag']['convert_not_enough_stellar_jade'])
    if not krutka_garant:
        return msg.reply(
            'Сначала выберите гарант питомца командой «<code>крутка гарант</code>»'
        )
    
    pets = await repo_biowar.get_my_pets(id)
    
    
    wish_text = (
        f'{link} крутит баннер <b>"Молитва на все"</b>\n'
        f'➖ {krutka_cost} ✨\n'
        f'Гарант пет(30 круток): <b>{krutka_garant["pet_garant_name"]}</b>'
    )
    my_pet = await repo_biowar.get_my_pet(id)
    pets = await repo_biowar.get_my_pets(id)
    
    await repo_biowar.update_bag_stellar_jade(id, krutka_cost, '-')
    
    wish = random.randint(1, 60)
    
    await repo_biowar.update_pet_garant_count(id, krutka_garant['krutki_count']+1)
    
    if wish == 60 or krutka_garant['krutki_count'] >= KRUTKA_GARANT:
        wish_rarity = 5
        await repo_biowar.update_pet_garant_count(id, 0)
        if krutka_garant['pet_garant_name'] in list(pets):
            pet = random.choice(list(tricks_biowar['pet']['pets_info']))
        elif krutka_garant['krutki_count'] < KRUTKA_GARANT:
            pet = random.choice(list(tricks_biowar['pet']['pets_info']))
        elif krutka_garant['krutki_count'] >= KRUTKA_GARANT:
            pet = krutka_garant['pet_garant_name']
        msg_animation = await msg.reply_animation(
            FSInputFile('media/5starwish.mp4', '5starwish.mp4'), caption=wish_text)
        await asyncio.sleep(6)
        await msg_animation.delete()
        if not any([p for p in pets if p['pet_name'].lower() == pet]):
            await repo_biowar.give_pet(id, pet, tricks_biowar['pet']['pets_info'][pet]['element'])

            happy_emoji = func.pet_current_happy_emoji(my_pet['happy'])
            
            pet_info = tricks_biowar['pet']['pets_info'][pet]
            text = tricks_biowar['pet']['get_my_pet'].format(
                pet_info['emoji'], pet.title(), pet_info['element_emoji'],
                pet_info['element'], happy_emoji, my_pet['happy'],
                '<i>' + pet_info['skill'] + '</i>',
                '<blockquote><i>' + pet_info['description'] + '</i></blockquote>'
            )
            
            pet_msg = await msg.answer_sticker(stickers['pet'][pet])

            await redis.set(f'epidemic_pet_owner_msg:{msg.chat.id}:{pet_msg.message_id}', id)
            await asyncio.sleep(0.1)
            
            await msg.answer(text + f'\n\nКол-во круток: <b>{krutka_garant["krutki_count"]}</b>')

        else:
            stellar_jade = random.randint(60, 160)
            text = (
                f'{link}, У вас уже существует этот пет или вы проиграли, поэтому вы получили:\n➕<u>{stellar_jade} звездного нефрита</u> ✨\n\n'
                f'- Вы можете потратить их на био-ресурсы командой <code>нефритсвап {stellar_jade}</code>\n\n'
                '<b>Баннер:</b> Молитва на все\n'
                f'Кол-во круток: <b>{krutka_garant["krutki_count"]+1}</b>'
            )
            await repo_biowar.update_bag_stellar_jade(id, 160, '+')
            await msg.answer(text)
    elif wish < 5:
        wish_rarity = 3
        stellar_jade = random.randint(60, 160)
        await repo_biowar.update_bag_stellar_jade(id, stellar_jade, '+')
        msg_animation = await msg.reply_animation(
            FSInputFile('media/4starwish.mp4', '4starwish.mp4'), caption=wish_text)
        await asyncio.sleep(6)
        await msg_animation.delete()
        text = (
            f'{link}, вы получили:\n➕<u>{stellar_jade} звездного нефрита</u> ✨\n\n'
            f'- Вы можете потратить их на био-ресурсы командой <code>нефритсвап {stellar_jade}</code>\n\n'
            '<b>Баннер:</b> Молитва на все\n'
            f'Кол-во круток: <b>{krutka_garant["krutki_count"]+1}</b>'
        )
        await msg.answer(text)
    else:
        wish_rarity = 1
        primogem = random.randint(150, 400)
        await repo_biowar.update_bag_primogem(id, primogem, '+')
        msg_animation = await msg.reply_animation(
            FSInputFile('media/1starwish.mp4', '1starwish.mp4'), caption=wish_text)
        await asyncio.sleep(6)
        await msg_animation.delete()
        text = (
            f'{link}, вы получили:\n➕<u>{primogem} примогемов</u> 💠\n'
            f'- Вы можете потратить их на био-ресурсы командой <code>примосвап {primogem}</code>\n\n'
            '<b>Баннер:</b> Молитва на все\n'
            f'Кол-во круток: <b>{krutka_garant["krutki_count"]+1}</b>'
        )
        await msg.answer(text)


async def garant_choice(msg: Message, repo_biowar: RequestsRepoBiowar, redis: Redis):
    
    user = msg.from_user
    pets = await repo_biowar.get_my_pets(user.id)

    text = tricks_biowar['pet']['get_my_pets']

    await msg.answer(text, reply_markup=global_pets_list_nav(user.id))

async def my_pets_garant_choose(call: CallbackQuery, callback_data: PetsGlobalListChoose, repo_biowar: RequestsRepoBiowar):
    
    user = call.from_user
    pet = callback_data.pet.lower()
    pet_emoji = tricks_biowar['pet']['pets_info'][pet]['emoji']
    
    # errors
    if user.id != callback_data.user_id:
        return await call.answer('Не для тебя моя кнопочка росла')
    
    await repo_biowar.add_data_krutka_garant(user.id)
    await repo_biowar.update_pet_garant(user.id, pet)
    await call.answer(f'{pet_emoji} Вы изменили вашего гарант питомца на {pet}')
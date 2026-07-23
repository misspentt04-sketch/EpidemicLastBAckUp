from aiogram.types import Message
from asyncmy.cursors import Cursor
from aiogram import Bot

from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types import CallbackQuery

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar
from core.utils.genai import gpt_thinks

from core import func

from humanize import intcomma
from datetime import datetime, timedelta

import asyncio
import random

async def my_event_information(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    msgt = msg.text
    
    backpack = await repo_biowar.get_event_backpack(id)
    total_lvl = 0

    for item, val in backpack.items():
        if item in tricks_biowar['event']['backpack_items_en2ru']:
            total_lvl += val

    event_info = (
        '<b>🎗 Информация о вашем ивенте</b>\n\n'
        
        f'📚 Общий уровень ваших предметов: <i>{total_lvl}</i>\n'
        
        '<i>✨ Подсчет наград в конце ивента до хэллоуина</i>'
    )
    await msg.answer(event_info)

async def event_biotop(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    
    biotop = await repo_biowar.get_event_biotop()
    
    biotop_list = func.get_biotop_event(biotop)
    
    l1 = '\n'.join(biotop_list[0:5:1])
    l2 = '\n'.join(biotop_list[5:10:1])
    l3 = '\n'.join(biotop_list[10:15:1])
    l4 = '\n'.join(biotop_list[15:20:1])
    l5 = '\n'.join(biotop_list[20:25:1])
    
    text = (
        tricks_biowar['biotops']['event'].format(
            l1,
            '\n<b>——— |🎗| — |🎗|—&gt</b>\n' + l2 if l2 else '',
            '\n<b>———|🥇| — |🥇|—&gt</b>\n' + l3 if l3 else '',
            '\n<b>——— |🥈| — |🥈|—&gt</b>\n' + l4 if l4 else '',
            '\n<b>——— |🥉| — |🥉|—&gt</b>\n' + l5 if l5 else '',
        )
    )
    
    await msg.answer(text)

async def send_valentinka(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    user_id = msg.from_user.id
    parts = msg.text.split()
    valentinka_type = parts[0].replace('.', '').replace('!', '').replace('/', '').lower()
    val = int(parts[1]) if parts[:2][-1].isdigit() else 1
    gift_to = func.reply_or_tag_geeter(msg)
    primogem_price = val*25
    stellar_jade_price = val*5
    comment = (f'<b>💬 Любовное послание:</b> <i>⌜{msg.text.splitlines()[1]}⌟</i>' if len(msg.text.splitlines()) > 1 else '')

    user = await repo_biowar.get_user(user_id)
    
    if gift_to == user_id:
        gift_to = await repo_biowar.get_random_user()
    else:
        gift_to = await repo_biowar.get_user(gift_to)
    
    bag = await repo_biowar.get_bag(user_id)
    
    heart = random.choice(['🩷','❤','🧡','💛','💚','🩵','💙','💜','🤍','❣','💕','💞','💓','💗','💖','💘','💝'])
    mention_to = func.entity_create_consider_username(gift_to)
    mention = func.entity_create_consider_username(user)
    
    current_date = datetime.now()
    now = current_date.strftime('%d.%m.%y')
    
    valentin_text = (
        '<b>💝—💖—💗—💘—💓—💖—💝</b>\n'
        '<blockquote><b>┌ {}:</b> «Моя любовь живёт в этих словах»\n'
        f'<b>├ Адресовано:</b> {mention_to}\n'
        '<b>├ Потрачено:</b> -{}{}\n'
        f'<b>└ Дата:</b> {now}</blockquote>\n'
        '<b>💝—💖—💗—💘—💓—💖—💝</b>\n\n'
        f'{f"{comment}\n\n" if comment else ""}'
        f'{heart} С любовью, от {mention}'
        
    )
    
    # errors
    if user['id'] == gift_to['id']:
        return await msg.answer(f'{heart} Увы... мне бы тоже хотелось получать валентинки')
    if comment and valentinka_type == 'открытка':
        return await msg.answer(f'{heart} Любовное послание возможно только в открытках-нефритках')
    
    if valentinka_type == 'открытка':
        if bag['primogem'] < primogem_price:
            return await msg.answer(tricks_biowar['bag']['not_enough_stellar_jade'])
        await repo_biowar.update_bag_primogem(user_id, primogem_price, '-')
        gifts = f"{val} Открыток" if val > 1 else "Открытка"
        valentin_text = valentin_text.format(gifts, primogem_price, '💠')
    if valentinka_type == 'нефритка':
        if bag['stellar_jade'] < stellar_jade_price:
            return await msg.answer(tricks_biowar['bag']['not_enough_stellar_jade'])
        await repo_biowar.update_bag_stellar_jade(user_id, stellar_jade_price, '-')
        gifts = f"{val} Нефриток" if val > 1 else "Нефритка"
        valentin_text = valentin_text.format(gifts, stellar_jade_price, '✨')
        val = val*5
    
    await repo_biowar.create_valentinka_column(user_id)
    await repo_biowar.send_valentinka(user_id, gift_to['id'], val)
    
    await msg.answer(valentin_text, disable_web_page_preview=True)
    try:
        await bot.send_message(gift_to['id'], valentin_text, disable_web_page_preview=True)
    except:
        pass
    
    
async def send_gift(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    user_id = msg.from_user.id
    gift_to = func.reply_or_tag_geeter(msg)
    stellar_jade_price = 8
    comment = (f'<b>🌸 Любовное послание:</b> <i>⌜{msg.text.splitlines()[1]}⌟</i>' if len(msg.text.splitlines()) > 1 else '')

    user = await repo_biowar.get_user(user_id)
    
    if gift_to == user_id:
        return
    else:
        gift_to = await repo_biowar.get_user(gift_to)
    
    bag = await repo_biowar.get_bag(user_id)
    
    heart = random.choice(['🩷','❤','🧡','💛','💚','🩵','💙','💜','🤍','❣','💕','💞','💓','💗','💖','💘','💝'])
    mention_to = func.entity_create_consider_username(gift_to)
    mention = func.entity_create_consider_username(user)
    
    current_date = datetime.now()
    now = current_date.strftime('%d.%m.%y')
    
    if bag['stellar_jade'] < stellar_jade_price:
        return await msg.answer(tricks_biowar['bag']['not_enough_stellar_jade'])
    
    stickers = []
    stickers_set = await bot.get_sticker_set('HelmetSkins_by_stickerparsebot')
    stickers_set1 = await bot.get_sticker_set('gifts_8_match')
    if random.randrange(1, 4) == 1:
        stickers.extend([i.file_id for i in stickers_set.stickers])
    stickers.extend([i.file_id for i in stickers_set1.stickers])
    
    sticker = random.choice(stickers)
    valentin_text = (
        '<b>🌷—💐—🌺—🌹—🌺—💐—🌷</b>\n'
        '<blockquote><b>┌ Подарок:</b> «Моя любовь живёт в этих словах»\n'
        f'<b>├ Адресовано:</b> {mention_to}\n'
        '<b>├ Потрачено:</b> -8✨\n'
        f'<b>└ Дата:</b> {now}</blockquote>\n'
        '<b>🌷—💐—🌺—🌹—🌺—💐—🌷</b>\n\n'
        f'{f"{comment}\n\n" if comment else ""}'
        f'{heart} С любовью, от {mention}'
        
    )
    
    await msg.answer_sticker(sticker)
    await asyncio.sleep(0.1)
    await msg.answer(valentin_text, disable_web_page_preview=True)
    await asyncio.sleep(0.1)
    try:
        await bot.send_sticker(gift_to['id'], sticker, message_effect_id='5159385139981059251')
        await bot.send_message(gift_to['id'], valentin_text, disable_web_page_preview=True, message_effect_id='5159385139981059251')
    except:
        pass


async def one_april_joke(msg: Message):
    
    text = (
        '❗️ Вы исключили себя из участия в игре «Био-войны»\n\n'
        'Весь игровой процесс, био-ресурсы, сообщения сброшены и удалены безвозвратно.'
    )
    
    await msg.answer(text)


async def aprelki(msg: Message, repo_biowar: RequestsRepoBiowar):
    
    await repo_biowar.add_my_aprelki(msg.from_user.id)
    me_aprelki = await repo_biowar.get_my_aprelki(msg.from_user.id)
    
    now = datetime.utcnow()
    
    # errors
    if me_aprelki['aprelki_next_time'] and now < datetime.fromtimestamp(me_aprelki['aprelki_next_time']):
        time_dif = func.diff_convert_timestamp_to_human(me_aprelki['aprelki_next_time'])
        return await msg.answer(f'🗝 Открыть пиратский сундук можно через {time_dif} таймер хаоса')
    
    ai_text = gpt_thinks('Ты — мастер абсурдного юмора, чёрного сарказма и неожиданных панчлайнов. Придумай 1 очень странную, но смешную шутку на тему био-войн, учёных и научных экспериментов. Шутка должна быть максимально нелепая, с элементами чёрного юмора и неожиданными сравнениями. Используй научный жаргон, доведённый до абсурда, ироничные отсылки и мрачноватый сарказм. Шутка — не больше 160 символов. Вот пример стиля: «Учёные создали вирус, превращающий людей в маркетологов. Пандемия началась ещё в 2010-м, но все думали, что это просто тренд»')
    
    aprelki = random.randint(1, 28)
    if random.randint(1, 28) == 1:
        aprelki = random.randint(50, 100)
        text = (
            f'<b>🔑 Какая удача! Вы открыли пиратский сундук</b>\n\n'
            f'☀️ <b>Лут +{aprelki}</b>. Теперь у вас <b>{aprelki+me_aprelki["aprelki"]}</b> апрелек\n\n'
            f'<blockquote><i>{ai_text}</i></blockquote>'
        )
    text = (
        f'<b>🗝 Вы открыли пиратский сундук</b>\n\n'
        f'☀️ <b>Лут +{aprelki}</b>. Теперь у вас <b>{aprelki+me_aprelki["aprelki"]}</b> апрелек\n\n'
        f'<blockquote><i>{ai_text}</i></blockquote>'
    )
    
    next_time_random_m = random.randint(30, 90)
    next_time = int((datetime.utcnow() + timedelta(minutes=next_time_random_m)).timestamp())
    
    await repo_biowar.setup_my_aprelki(msg.from_user.id, aprelki+me_aprelki['aprelki'], next_time)
    
    await msg.answer_sticker('CAACAgIAAxkBAAEdsSFn6Svx4dcvsA-9AAEYQjg4ekqglocAAvxrAAJ3_ElLVOLxf-vvAQU2BA')
    await asyncio.sleep(0.1)
    await msg.answer(text)
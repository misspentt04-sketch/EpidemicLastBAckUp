from aiogram.types import Message
from aiogram import Bot

from core.data.icons import BagIco
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar, Const
from core import func

import html

# 1 нефрит - 5 примо
COURSE_STELLAR_JADE_TO_PRIMO = 5

async def get_bag(
        msg: Message,
        repo_biowar: RequestsRepoBiowar,

):
    id = msg.from_user.id
    bag = await repo_biowar.get_bag(id)
    user = await repo_biowar.get_user(id)

    primogem = bag['primogem']
    stellar_jade = bag['stellar_jade']

    link = func.ping_link(id, user['full_name'])

    text = tricks_biowar['bag']['get_bag'].format(primogem=primogem, stellar_jade=stellar_jade, link=link)

    await msg.answer(text)


async def send_currency(msg: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    id = msg.from_user.id
    parts = msg.text.split()
    amount = int(parts[1]) if parts[:2][-1].isdigit() else 1
    amount_ = amount
    receiver = func.reply_or_tag_geeter(msg)
    comment = ' '.join(msg.text.split()[3:] if func.link_getter(msg.text) else msg.text.split()[2:])
    if len(comment) >= 1:
        comment = Const.COMMENT.format(comment)
    commission = 0
    commission_text = ''

    # errors
    if amount == 0:
        return

    sender_bag = await repo_biowar.get_bag(id)
    receiver_user = await repo_biowar.get_user(receiver)

    if amount >= 20:
        commission = int(amount * 0.05)
    else:
        commission = 1
    amount = amount+commission
    commission_text += f'<b>Комиссия:</b> {commission} нефрита'
    
    # errors
    if not receiver_user:
        return await msg.answer(tricks_biowar['text']['not_info_about_user'])
    if receiver_user['id'] == id:
        return await msg.answer(tricks_biowar['bag']['you_cant_send_to_yourself'])
    if sender_bag['stellar_jade'] < amount:
        return await msg.answer(tricks_biowar['bag']['not_enough_stellar_jade'].format(commission_text))
    
    receiver_mention = func.entity_create(receiver_user['id'], receiver_user['full_name'])
    sender_mention = func.entity_create(sender_bag['id'], html.escape(msg.from_user.full_name))

    await repo_biowar.update_bag_stellar_jade(id, amount, '-')
    await repo_biowar.update_bag_stellar_jade(receiver_user['id'], amount_)

    sender_text = tricks_biowar['bag']['send_currency'].format(receiver_mention, amount_, comment, commission_text)
    receiver_text = tricks_biowar['bag']['get_currency'].format(sender_mention, amount_, comment)

    await msg.answer(sender_text)
    await bot.send_message(receiver_user['id'], receiver_text)


async def convert_stellar_jade_to_primo(msg: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    id = msg.from_user.id
    parts = msg.text.split()
    count = int(parts[1]) if parts[:2][-1].isdigit() else 1

    # errors
    if count == 0:
        return

    bag = await repo_biowar.get_bag(id)

    stellar_jade = bag['stellar_jade']

    jade = count
    primo = jade * 5

    if jade > stellar_jade:
        return msg.reply(tricks_biowar['bag']['convert_not_enough_stellar_jade'])

    await repo_biowar.update_bag_primogem(id, primo, "+")
    await repo_biowar.update_bag_stellar_jade(id, jade, '-')

    await msg.reply(
        tricks_biowar['bag']['convert_stellar_jade_to_primo'].format(
            jade=jade, primo=primo)

    )

async def convert_stellar_jade_to_bio_resource(msg: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    id = msg.from_user.id
    parts = msg.text.split()
    count = int(parts[1]) if parts[:2][-1].isdigit() else 1

    # errors
    if count == 0:
        return

    bag = await repo_biowar.get_bag(id)

    stellar_jade = bag['stellar_jade']

    jade = count
    bio_resource = jade * 1500

    if jade > stellar_jade:
        return msg.reply(tricks_biowar['bag']['convert_not_enough_stellar_jade'])

    lab = await repo_biowar.get_info_user_lab(id)

    await repo_biowar.update_lab_skill_val(id, 'bio_resource', lab['bio_resource']+bio_resource)
    await repo_biowar.update_bag_stellar_jade(id, jade, '-')

    await msg.reply(
        tricks_biowar['bag']['convert_stellar_jade_to_bio_resource'].format(
            jade=jade, bio_resource=bio_resource)

    )


async def convert_primogem_to_bio_resource(msg: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    id = msg.from_user.id
    parts = msg.text.split()
    count = int(parts[1]) if parts[:2][-1].isdigit() else 1

    # errors
    if count == 0:
        return

    bag = await repo_biowar.get_bag(id)

    primogem = bag['primogem']

    primo = count
    bio_resource = primo * 300

    if primo > primogem:
        return msg.reply(tricks_biowar['bag']['convert_not_enough_stellar_jade'])

    lab = await repo_biowar.get_info_user_lab(id)

    await repo_biowar.update_lab_skill_val(id, 'bio_resource', lab['bio_resource']+bio_resource)
    await repo_biowar.update_bag_primogem(id, primo, "-")

    await msg.reply(
        tricks_biowar['bag']['convert_primogem_to_bio_resource'].format(
            primogem=primo, bio_resource=bio_resource)

    )
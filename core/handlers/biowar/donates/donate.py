from aiogram.types import (
    Message, LabeledPrice, PreCheckoutQuery,
    InlineKeyboardMarkup, CallbackQuery, LinkPreviewOptions
)
from aiogram.filters import CommandObject
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ChatType
from aiogram import Bot

from asyncmy.cursors import Cursor
from aiocryptopay import AioCryptoPay
from aiocryptopay.api import Invoice

from core.keyboards.inline.donate import (
    donate_list, donate_list_crypto, donate_redirect_to_pm, donate_redirect_to_cryptobot
)
from core.utils.callbackdata import DonateList, DonateListCrypto
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.texttriggers import deep_links
from core.data.icons import LabIco, OtherIco
from core.data.tricks.tricks_biowar import tricks_biowar

from core.cryptopay import CryptoPay
from core.settings import settings
from core import func

from humanize import intcomma

import html
import asyncio

async def donate_func(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar, deep_link: int=False):
    
    if isinstance(msg, CallbackQuery):
        m = msg.message
    else:
        m = msg
    
    id = msg.from_user.id
    bag = await repo_biowar.get_bag(id)
    user_donate = await repo_biowar.get_user_donate(id)
    
    mention = func.entity_create(id, html.escape(msg.from_user.full_name), deep_links['mention_click'])
    
    if m.chat.type != ChatType.PRIVATE:
        return await msg.answer(
            tricks_biowar['donate']['donate_in_group'].format(mention),
            reply_markup=donate_redirect_to_pm()
        )
    
    text = tricks_biowar['donate']['donate_list'].format(mention)
    
    await m.answer(text, reply_markup=donate_list(user_donate), disable_web_page_preview=True)
    if deep_link:
        await m.delete()


async def donate(msg: Message, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    await donate_func(msg, bot, db, repo_biowar)

async def donate_inline(call: CallbackQuery, bot: Bot, db: Cursor, repo_biowar: RequestsRepoBiowar):
    
    await donate_func(call, bot, db, repo_biowar)

async def donate_send(
    call: CallbackQuery,
    callback_data: DonateList
):
    amount = callback_data.stars_count

    prices = [LabeledPrice(label="XTR", amount=amount)]
    await call.message.answer_invoice(
        title=tricks_biowar['donate']['invoice_title'],
        description=tricks_biowar['donate']['invoice_description'].format(amount * 3),
        prices=prices,
        provider_token='',
        payload=f"{amount}_{callback_data.kit}",
        currency="XTR",
    )
    await call.answer()

async def donate_on_pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery,
):
    await pre_checkout_query.answer(ok=True)

async def donate_successful_payment(msg: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    
    id = msg.from_user.id
    user_donate = await repo_biowar.get_user_donate(id)
    
    amount = msg.successful_payment.total_amount
    kit = msg.successful_payment.invoice_payload.split('_')[1]
    user_donate = await repo_biowar.get_user_donate(id)
    is_kit = user_donate[f'kit{kit}']
    mention = func.entity_create(id, html.escape(msg.from_user.full_name), deep_links['mention_click'])
    stellar_jade_give = amount*3 if is_kit else amount*3*2
    
    text = tricks_biowar['donate']['payment_successful'].format(
        mention, (f'+{amount*3}' if is_kit else f'{amount*3}+{amount*3} бонус!')
    )
    
    # for testing purpose only
    # await bot.refund_star_payment(
    #     user_id=id,
    #     telegram_payment_charge_id=msg.successful_payment.telegram_payment_charge_id,
    # )
    
    await repo_biowar.change_kit_donate(id, kit, 1)
    await repo_biowar.update_bag_stellar_jade(id, stellar_jade_give)
    
    await msg.answer_sticker(tricks_biowar['donate']['payment_successful_sticker'])
    await asyncio.sleep(1)
    await msg.answer(text, message_effect_id='5159385139981059251')

async def paysupport(
    message: Message,
):
    await message.answer(
        tricks_biowar['donate']['paysupport'],
        disable_web_page_previw=True,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

async def donate_refund(
    msg: Message,
    bot: Bot,
    command: CommandObject,
):
    transaction_id = command.args
    id = msg.from_user.id
    
    # errors
    if transaction_id is None:
        return await msg.answer(tricks_biowar['donate']['refund_no_code_provided'])
    
    return await msg.answer('Возврат средств по нашему регламенту ToS не предусмотрен ✨')
    
    # for testing purpose only
    # try:
    #     await bot.refund_star_payment(id, transaction_id)
    #     await msg.answer(tricks_biowar['donate']['refund_successful'])
    # except TelegramBadRequest as err:
    #     if "CHARGE_NOT_FOUND" in err.message:
    #         text = tricks_biowar['donate']['refund_code_not_found']
    #     elif "CHARGE_ALREADY_REFUNDED" in err.message:
    #         text = tricks_biowar['donate']['refund_already_refunded']
    #     else:
    #         text = tricks_biowar['donate']['refund_code_not_found']
    #     return await msg.answer(text)

async def donate_crypto(call: CallbackQuery, callback_data: DonateList, repo_biowar: RequestsRepoBiowar):
    
    id = call.from_user.id
    user_donate = await repo_biowar.get_user_donate(id)
    
    mention = func.entity_create(id, html.escape(call.from_user.full_name), deep_links['mention_click'])
    
    text = tricks_biowar['donate']['donate_list_crypto'].format(mention)
    
    await call.message.edit_text(text, reply_markup=donate_list_crypto(user_donate), disable_web_page_preview=True)
    await call.answer()

async def donate_send_crypto(call: CallbackQuery, callback_data: DonateListCrypto, repo_biowar: RequestsRepoBiowar, crypto: AioCryptoPay):
    
    id = call.from_user.id
    currency = call.message.text
    amount = callback_data.stars_count
    user_donate = await repo_biowar.get_user_donate(id)
    is_kit = user_donate[f'kit{callback_data.kit}']
    stellar_jade_give = amount*3 if is_kit else amount*3*2
    mention = func.entity_create(call.from_user.id, html.escape(call.from_user.full_name), deep_links['mention_click'])
    
    fiat_invoice = await crypto.create_invoice(
        amount=amount*1.31,
        fiat='RUB',
        accepted_assets=['USDT', 'TON', 'NOT', 'BTC', 'ETH'],
        currency_type='fiat',
        hidden_message=tricks_biowar['donate']['crypto_pay_hidden_message'],
        expires_in=120
    )
    invoice_url = fiat_invoice.bot_invoice_url
    invoice_id = fiat_invoice.invoice_id
    
    await call.message.answer(
        tricks_biowar['donate']['redirect_to_cryptobot'],
        reply_markup=donate_redirect_to_cryptobot(amount, fiat_invoice.bot_invoice_url, callback_data.kit, user_donate),
        disable_web_page_preview=True,
    )
    
    while True:
        await asyncio.sleep(3)
        status = await CryptoPay.get_status(fiat_invoice.invoice_id)
        if status == 'paid':
            text = tricks_biowar['donate']['payment_successful'].format(
                mention, (f'+{amount*3}' if is_kit else f'+{amount*3}+{amount*3} бонус!')
            )
            sticker = tricks_biowar['donate']['payment_successful_sticker']
            effect_id = '5159385139981059251'
            break
        elif status == 'expired':
            text = tricks_biowar['donate']['payment_unsuccessful'].format(mention)
            sticker = tricks_biowar['donate']['payment_unsuccessful_sticker']
            effect_id = None
            break
    
    if status == 'paid':
        await repo_biowar.change_kit_donate(id, callback_data.kit, 1)
        await repo_biowar.update_bag_stellar_jade(id, stellar_jade_give)
    
    await call.message.answer_sticker(sticker)
    await asyncio.sleep(1)
    await call.message.answer(text, message_effect_id=effect_id)



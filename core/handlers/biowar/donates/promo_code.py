from aiogram.types import Message

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.tricks.tricks_biowar import tricks_biowar
from core import func


async def promo_code_use(msg: Message, repo_biowar: RequestsRepoBiowar):
    
    promo_text = ' '.join(msg.text.split()[1:])
    user_id = msg.from_user.id
    
    promo = await repo_biowar.get_promocode(promo_text)
    
    # errors
    if not promo:
        return await msg.answer(tricks_biowar['promo_code']['does_not_exist'].format(promo_text))
    
    user_promo = await repo_biowar.get_user_promo(user_id, promo_text)
    
    # errors
    if user_promo:
        return await msg.answer(tricks_biowar['promo_code']['already_use'])
    
    if promo['type'] == 'stellar_jade':
        await repo_biowar.update_bag_stellar_jade(user_id, promo['val_count'])
        text = tricks_biowar['promo_code']['stellar_jade'].format(promo_text, promo['val_count'])
    if promo['type'] == 'primogem':
        await repo_biowar.update_bag_primogem(user_id, promo['val_count'])
        text = tricks_biowar['promo_code']['primogem'].format(promo_text, promo['val_count'])
    
    await repo_biowar.user_add_promo_usage(user_id, promo['promo_code'])
    await repo_biowar.delete_promo(promo['id'])
    
    await msg.answer(text)

async def promo_code_show(msg: Message, repo_biowar: RequestsRepoBiowar):
    
    promo_count, promo_codes = await repo_biowar.show_promocodes()
    
    promo_list = func.get_promo_list(promo_codes, promo_count)
    text = tricks_biowar['promo_code']['show_promo_list'].format('\n'.join(promo_list))
    
    await msg.answer(text)
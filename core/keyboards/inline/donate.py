from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.utils.callbackdata import DonateList, DonateListCrypto
from core.settings import settings


def donate_list(user_donate: dict):
    kb = InlineKeyboardBuilder()
    
    stars_count_ = [
        60, 300, 980,
        1980, 3280, 6480,
    ]
    
    stars_count = []
    
    for n, k in enumerate(stars_count_, 1):
        if user_donate[f'kit{n}']:
            stars_count.append([f'+{k}', False])
        else:
            stars_count.append([f'{k}+{k}', True])
    
    kb.button(text=f'✨ {stars_count[0][0]}', callback_data=DonateList(kit=1, stars_count=20))
    kb.button(text=f'✨ {stars_count[1][0]}', callback_data=DonateList(kit=2, stars_count=100))
    kb.button(text=f'✨ {stars_count[2][0]}', callback_data=DonateList(kit=3, stars_count=325))
    kb.button(text=f'✨ {stars_count[3][0]}', callback_data=DonateList(kit=4, stars_count=660))
    kb.button(text=f'✨ {stars_count[4][0]}', callback_data=DonateList(kit=5, stars_count=1080))
    kb.button(text=f'✨ {stars_count[5][0]}', callback_data=DonateList(kit=6, stars_count=2160))
    kb.button(text=f'Оплата через CryptoBot', callback_data=DonateList(action='donate_crypto_menu', kit=0, stars_count=0))
    
    kb.adjust(3,3,2),
    return kb.as_markup(resize_keyboard=True)

def donate_list_crypto(user_donate: dict):
    kb = InlineKeyboardBuilder()
    
    stars_count_ = [
        60, 300, 975,
        1980, 3240, 6480,
    ]
    
    stars_count = []
    
    for n, k in enumerate(stars_count_, 1):
        if user_donate[f'kit{n}']:
            stars_count.append([f'+{k}', False])
        else:
            stars_count.append([f'{k}+{k}', True])
    
    kb.button(text=f'✨ {stars_count[0][0]}', callback_data=DonateListCrypto(kit=1, stars_count=20))
    kb.button(text=f'✨ {stars_count[1][0]}', callback_data=DonateListCrypto(kit=2, stars_count=100))
    kb.button(text=f'✨ {stars_count[2][0]}', callback_data=DonateListCrypto(kit=3, stars_count=325))
    kb.button(text=f'✨ {stars_count[3][0]}', callback_data=DonateListCrypto(kit=4, stars_count=660))
    kb.button(text=f'✨ {stars_count[4][0]}', callback_data=DonateListCrypto(kit=5, stars_count=1080))
    kb.button(text=f'✨ {stars_count[5][0]}', callback_data=DonateListCrypto(kit=6, stars_count=2160))
    kb.button(text=f'💚 Вернуться назад', callback_data=DonateListCrypto(action='donate_main_menu', kit=0, stars_count=0))
    
    kb.adjust(3,3,2),
    return kb.as_markup(resize_keyboard=True)

def donate_redirect_to_pm():
    kb = InlineKeyboardBuilder()
    
    kb.button(
        text='✨ Задонатить в эпидемик',
        url=f'https://t.me/{settings.bots.bot_username}?start=donate'
    )
    
    return kb.as_markup(resize_keyboard=True)


def donate_redirect_to_cryptobot(amount: int, crypto_url: str, kit: int, user_donate: dict):
    kb = InlineKeyboardBuilder()
    
    amount_ = (amount*3 if user_donate[f'kit{kit}'] else f'{amount*3}+{amount*3}')
    
    kb.button(
        text=f'✨ Купить {amount_} нефритов',
        url=crypto_url
    )
    
    return kb.as_markup(resize_keyboard=True)
from aiogram.exceptions import TelegramBadRequest
import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from core.data.tricks.themes_data import THEMES_DATA, THEME_ID_MAP

router = Router()

SHOP_THEMES = {
    "police": {"id": 1, "price": 2500, "desc": "🚨 Задержания, КПЗ и выслуга лет"},
    "it": {"id": 2, "price": 3000, "desc": "💻 Хакерские атаки и ботнеты"},
    "army": {"id": 3, "price": 2800, "desc": "🪖 Гарнизоны, приказы и гауптвахты"},
    "mafia": {"id": 4, "price": 4000, "desc": "🕶 Рэкет, общак и крышевание"},
    "zombie": {"id": 5, "price": 3500, "desc": "🧟 Убежища, вирусы и мутанты"},
    "cyberpunk": {"id": 6, "price": 5000, "desc": "⚡ Нейро-сети, чипы и импланты"},
    "space": {"id": 7, "price": 4500, "desc": "🚀 Космические станции и дроны"},
    "fantasy": {"id": 8, "price": 3200, "desc": "🛡 Цитадели, магия и темницы"},
    "medic": {"id": 9, "price": 4800, "desc": "🏥 Госпиталя, вирусы и карантины"}
}

REVERSE_THEME_ID_MAP = {v: k for k, v in THEME_ID_MAP.items()}

THEME_COMMANDS = ["т", "темы", "тема"]

def check_theme_cmd(text: str) -> bool:
    if not text:
        return False
    text = text.strip().lower()
    for cmd in THEME_COMMANDS:
        for prefix in [".", "!", "/", "?", ""]:
            if text == f"{prefix}{cmd}":
                return True
    return False

def normalize_theme_key(raw_theme) -> str:
    if raw_theme is None:
        return "default"
    if isinstance(raw_theme, int) or (isinstance(raw_theme, str) and raw_theme.isdigit()):
        return THEME_ID_MAP.get(int(raw_theme), "default")
    return str(raw_theme).lower()

async def get_user_theme(db, user_id: int) -> str:
    if not db:
        return "default"
    try:
        query = "SELECT active_theme FROM Users WHERE id = %s"
        await db.execute(query, (user_id,))
        res = await db.fetchone()
        if res:
            raw = res.get("active_theme") if isinstance(res, dict) else res[0]
            return normalize_theme_key(raw)
    except Exception as e:
        print(f"[THEMES GET ACTIVE ERROR] {e}")
    return "default"

async def set_user_theme(db, user_id: int, theme_id: str):
    if not db:
        return
    try:
        db_val = REVERSE_THEME_ID_MAP.get(theme_id, theme_id)
        query = "UPDATE Users SET active_theme = %s WHERE id = %s"
        await db.execute(query, (db_val, user_id))
    except Exception as e:
        print(f"[THEMES SET ERROR] {e}")

async def get_user_bought_themes(db, user_id: int) -> list:
    if not db:
        return ["default"]
    try:
        query = "SELECT bought_themes FROM Users WHERE id = %s"
        await db.execute(query, (user_id,))
        res = await db.fetchone()
        if res:
            raw = res.get("bought_themes") if isinstance(res, dict) else res[0]
            if raw:
                bought_raw = json.loads(raw) if isinstance(raw, str) else raw
                normalized = []
                for t in bought_raw:
                    normalized.append(normalize_theme_key(t))
                if "default" not in normalized:
                    normalized.append("default")
                return normalized
    except Exception as e:
        print(f"[THEMES GET BOUGHT ERROR] {e}")
    return ["default"]

async def save_bought_themes(db, user_id: int, bought_list: list):
    if not db:
        return
    try:
        db_list = [REVERSE_THEME_ID_MAP.get(t, t) for t in bought_list if t != "default"]
        query = "UPDATE Users SET bought_themes = %s WHERE id = %s"
        await db.execute(query, (json.dumps(db_list), user_id))
    except Exception as e:
        print(f"[THEMES SAVE BOUGHT ERROR] {e}")

async def get_user_coins(db, user_id: int) -> int:
    if not db:
        return 0
    try:
        query = "SELECT epicoins FROM Lab WHERE lab_id = %s"
        await db.execute(query, (user_id,))
        res = await db.fetchone()
        if res and isinstance(res, dict) and "epicoins" in res:
            return int(res["epicoins"] or 0)
    except Exception as e:
        print(f"[THEMES GET EPICOINS ERROR] {e}")
    return 0

async def deduct_user_coins(db, user_id: int, amount: int):
    if not db:
        return
    try:
        query = "UPDATE Lab SET epicoins = epicoins - %s WHERE lab_id = %s"
        await db.execute(query, (amount, user_id))
    except Exception as e:
        print(f"[THEMES DEDUCT EPICOINS ERROR] {e}")

async def get_main_menu(db, user_id: int):
    active_theme = await get_user_theme(db, user_id)
    bought_themes = await get_user_bought_themes(db, user_id)
    theme_info = THEMES_DATA.get(active_theme, {})
    current_name = theme_info.get("name", "⚙️ Стандартная")

    text = (
        "🎨 <b>Управление Темами оформления</b>\n\n"
        f"🔹 <b>Активная тема:</b> {current_name}\n"
        f"📦 <b>Куплено тем:</b> {len(bought_themes)} / {len(SHOP_THEMES) + 1}\n\n"
        "<i>Выберите нужный раздел ниже:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎒 Мои темы", callback_data="my_themes_menu"),
            InlineKeyboardButton(text="🛒 Магазин тем", callback_data="shop_themes_menu")
        ]
    ])
    return text, kb

async def get_my_themes_menu(db, user_id: int):
    active_theme = await get_user_theme(db, user_id)
    bought_themes = await get_user_bought_themes(db, user_id)
    theme_info = THEMES_DATA.get(active_theme, {})
    current_name = theme_info.get("name", "⚙️ Стандартная")

    text = (
        "🎒 <b>Ваши приобретённые темы:</b>\n\n"
        f"🔹 <b>Сейчас активна:</b> {current_name}\n\n"
        "<i>Нажмите на тему ниже, чтобы быстро её установить:</i>"
    )

    buttons = []
    
    # Отображаем ВСЕ темы из купленных пользователем
    for theme_id in bought_themes:
        info = THEMES_DATA.get(theme_id, {})
        name = info.get("name", theme_id.capitalize())
        prefix = "✅ " if active_theme == theme_id else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{name}", callback_data=f"set_theme:{theme_id}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_themes_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return text, kb

async def get_shop_themes_menu(db, user_id: int):
    bought_themes = await get_user_bought_themes(db, user_id)
    user_coins = await get_user_coins(db, user_id)

    text = (
        "🛒 <b>Каталог тем для покупки:</b>\n\n"
        f"🪙 <b>Ваши эпикоины:</b> {user_coins:,}\n\n"
        "<i>Нажмите на тему в списке ниже, чтобы сразу купить или установить её:</i>"
    )

    buttons = []
    for theme_id, info in SHOP_THEMES.items():
        theme_data = THEMES_DATA.get(theme_id, {})
        name = theme_data.get("name", theme_id)
        price = info.get("price", 0)

        if theme_id in bought_themes:
            btn_text = f"✅ {name} (Куплено)"
            callback = f"set_theme:{theme_id}"
        else:
            btn_text = f"🛒 {name} — {price:,} эпикоинов"
            callback = f"buy_theme:{theme_id}"

        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=callback)])

    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_themes_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return text, kb

@router.message(F.text.func(check_theme_cmd))
async def themes_menu_handler(message: Message, db=None):
    text, kb = await get_main_menu(db, message.from_user.id)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "main_themes_menu")
async def main_themes_callback(call: CallbackQuery, db=None):
    text, kb = await get_main_menu(db, call.from_user.id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest:
        await call.answer()
    await call.answer()

@router.callback_query(F.data == "my_themes_menu")
async def my_themes_callback(call: CallbackQuery, db=None):
    text, kb = await get_my_themes_menu(db, call.from_user.id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest:
        await call.answer()
    await call.answer()

@router.callback_query(F.data == "shop_themes_menu")
async def shop_themes_callback(call: CallbackQuery, db=None):
    text, kb = await get_shop_themes_menu(db, call.from_user.id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest:
        await call.answer()
    await call.answer()

@router.callback_query(F.data.startswith("set_theme:"))
async def set_theme_callback(call: CallbackQuery, db=None):
    theme_id = call.data.split(":")[1]
    bought_themes = await get_user_bought_themes(db, call.from_user.id)

    if theme_id not in bought_themes:
        await call.answer("❌ Эта тема вам не принадлежит!", show_alert=True)
        return

    await set_user_theme(db, call.from_user.id, theme_id)
    theme_info = THEMES_DATA.get(theme_id, {})
    theme_name = theme_info.get("name", theme_id)

    text, kb = await get_my_themes_menu(db, call.from_user.id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest:
        await call.answer()
    await call.answer(f"✅ Установлена тема: {theme_name}", show_alert=False)

@router.callback_query(F.data.startswith("buy_theme:"))
async def buy_theme_callback(call: CallbackQuery, db=None):
    theme_id = call.data.split(":")[1]
    user_id = call.from_user.id

    if theme_id not in SHOP_THEMES:
        await call.answer("❌ Тема не найдена!", show_alert=True)
        return

    bought_themes = await get_user_bought_themes(db, user_id)
    if theme_id in bought_themes:
        await call.answer("✅ У вас уже есть эта тема!", show_alert=True)
        return

    price = SHOP_THEMES[theme_id]["price"]
    user_coins = await get_user_coins(db, user_id)

    if user_coins < price:
        await call.answer(f"❌ Недостаточно эпикоинов! У вас: {user_coins:,}, требуется: {price:,}", show_alert=True)
        return

    await deduct_user_coins(db, user_id, price)
    bought_themes.append(theme_id)
    await save_bought_themes(db, user_id, bought_themes)
    await set_user_theme(db, user_id, theme_id)

    theme_name = THEMES_DATA.get(theme_id, {}).get("name", theme_id)
    await call.answer(f"🎉 Вы успешно купили и установили тему: {theme_name}!", show_alert=True)

    text, kb = await get_shop_themes_menu(db, user_id)
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except TelegramBadRequest:
        await call.answer()


async def get_theme_text(db, user_id: int, text_key: str) -> str:
    active_theme = await get_user_theme(db, user_id)
    from core.data.tricks.themes_data import get_theme_text as get_raw_theme_text
    return get_raw_theme_text(active_theme, text_key)

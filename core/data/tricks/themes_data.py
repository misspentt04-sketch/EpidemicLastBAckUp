import json

# ==================== 0. СТАНДАРТНАЯ ТЕМА (DEFAULT) ====================
DEFAULT_THEME_DATA = {
    "name": "⚙️ Стандартная",
    "lab_dossier": (
        "📩 <b>Досье лаборатории {lab_name}:</b>\n"
        "Руководитель — {user_mention}\n"
        "{corp_name}\n"
        "🏷 <b>Имя патогена:</b> {pathogen_name}\n"
        "🧪 <b>Готовых патогенов:</b> {pathogens}/{max_pathogens}\n"
        "🧑‍🎤 <b>Квалификация учёных:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Характеристика ]——\n"
        "💉 Заразность: {infect_lvl} ур\n"
        "🪬 Иммунитет: {immunity_lvl} ур\n"
        "💊 Летальность: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🕵️‍♂️ Служба безопасности: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID лаборатории: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Запасы — реагентов ]——\n"
        "☣️ Опыт: {bio_experience}\n"
        "🧬 Ресурсы: {bio_resource}\n"
        "⏱ <i>Ежедневная премия через: Каждый день в 12.00 и 00.00</i></blockquote>"
        "🤒 Заражённых: {victims_count}\n"
        "😷 Своих болезней: {illnesses_count}"
    ),
    "infect_success": (
        "☣️ <b>УСПЕШНОЕ ЗАРАЖЕНИЕ!</b>\n\n"
        "Лаборатория {attacker_mention} успешно заразила {target_mention}!\n"
        "🦠 Применен патоген: <b>«{pathogen_name}»</b>\n\n"
        "📊 <b>Результаты атаки:</b>\n"
        "• Время лихорадки: <b>{fever_time}</b> мин.\n"
        "• Срок действия: <b>{expire_days}</b> дн.\n"
        "• Получено опыта: <b>+{exp_gain} EXP</b>\n\n"
        "✨ <i>Захвачено био-ресурсов: +{res_gain}</i>"
    ),
    "infect_failed": (
        "🛡 <b>АТАКА ОТБИТА!</b>\n\n"
        "Защитные системы «{target_mention}» сдержали инфекцию.\n"
        "Патоген не смог преодолеть высокий иммунитет хоста.\n\n"
        "⚡ <b>Данные разведки:</b>\n"
        "• Оставшиеся патогены: <b>{pathogens_left}</b>\n"
        "• Вероятность успеха: <b>{penetration_chance}%</b>\n"
        "• Статус: <i>Инфекция нейтрализована.</i>"
    ),
    "infected_you": (
        "🤢 <b>ВЫ ЗАРАЖЕНЫ!</b>\n\n"
        "Лаборатория {attacker_mention} провела успешную атаку на вашу систему!\n\n"
        "🔒 Время лихорадки: <b>{fever_time}</b> мин.\n"
        "⚙️ Длительность: <b>{expire_days}</b> дн."
    ),
    "sb_report": (
        "👁 Ваша служба безопасности нейтрализовала попытку заражения от {attacker_mention}."
    ),
    "victims_list_title": "🔒 <b>Зараженные лаборатории:</b>\n",
    "cases_menu": (
        "📦 <b>Контейнеры патогенов:</b>\n\n"
        "🪙 <b>Баланс:</b> {epicoins} эпикоинов\n"
        "📦 <b>Обычный контейнер:</b> {case1} шт.\n"
        "💎 <b>Элитный контейнер:</b> {case2} шт."
    )
}

# ==================== 1. АДМИНСКАЯ ТЕМА (ADMIN) ====================
ADMIN_THEME_DATA = {
    "name": "👑 Админ-панель",
    "lab_dossier": (
        "👑 <b>Админ-панель:</b>\n"
        "Создатель — {user_mention}\n"
        "{corp_name}\n"
        "🏷 Терминал: {pathogen_name}\n"
        "⚡ Активных потоков: {pathogens}/{max_pathogens}\n"
        "⚙️ Уровень доступа: {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Системный мониторинг ]——\n"
        "🔥 Мощность ядра: {infect_lvl} ур\n"
        "🛡 Защита хоста: {immunity_lvl} ур\n"
        "🔒 Изоляция процессов: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "👁 Спец-контроль: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID админа: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Системные ресурсы ]——\n"
        "⚡ Опыт: {bio_experience}\n"
        "📦 Логи: {bio_resource}\n"
        "⏰ Авто-бэкап: Каждый день в 12.00 и 00.00</blockquote>"
        "🔒 Заблокировано процессов: {victims_count}\n"
        "📜 Инцидентов: {illnesses_count}"
    ),
    "infect_success": (
        "👑 <b>ПРИМЕНЕНИЕ АДМИНИСТРАТИВНЫХ САНКЦИЙ!</b>\n\n"
        "Администратор {attacker_mention} применил протокол ограничений к {target_mention}.\n"
        "🔒 Закрепленный протокол: <b>«{pathogen_name}»</b>\n\n"
        "⚙️ <b>Параметры блокировки:</b>\n"
        "• Время изоляции: <b>{fever_time}</b> мин.\n"
        "• Срок действия санкций: <b>{expire_days}</b> дн.\n"
        "• Прирос уровня доступа: <b>+{exp_gain} EXP</b>\n\n"
        "✨ <i>Изъяты административные ресурсы: +{res_gain}</i>"
    ),
    "infect_failed": (
        "🛡 <b>ОТКАЗ В ДОСТУПЕ — ОШИБКА АВТОРИЗАЦИИ!</b>\n\n"
        "Система безопасности хоста «{target_mention}» отклонила запрос.\n"
        "Протокол санкций не был активирован из-за высокого уровня защиты.\n\n"
        "⚡ <b>Лог сервера:</b>\n"
        "• Доступных попыток: <b>{pathogens_left}</b>\n"
        "• Расчётный шанс пробития: <b>{penetration_chance}%</b>\n"
        "• Статус: <i>Access Denied (Code 403).</i>"
    ),
    "infected_you": (
        "⛔️ <b>К ВАМ ПРИМЕНЕНЫ САНКЦИИ!</b>\n\n"
        "Администратор {attacker_mention} ограничил ваши права доступа!\n\n"
        "🔒 Время изоляции: <b>{fever_time}</b> мин.\n"
        "⚙️ Срок действия: <b>{expire_days}</b> дн."
    ),
    "sb_report": (
        "👁 Спец-контроль зафиксировал и отразил несанкционированный запрос от {attacker_mention}."
    ),
    "victims_list_title": "🔒 <b>Список изолированных узлов:</b>\n",
    "cases_menu": (
        "📦 <b>Контейнеры разработчика:</b>\n\n"
        "🪙 <b>Баланс:</b> {epicoins} эпикоинов\n"
        "📦 <b>Пакет обновлений (Кейс 1):</b> {case1} шт.\n"
        "💎 <b>Админ-бокс (Кейс 2):</b> {case2} шт."
    )
}

def make_theme(name, dossier_title, target_title, pathogen_label, infect_title, fail_title):
    t = DEFAULT_THEME_DATA.copy()
    t["name"] = name
    t["lab_dossier"] = (
        f"{dossier_title}\n"
        "Владелец — {user_mention}\n"
        "{corp_name}\n"
        f"{pathogen_label}: {{pathogen_name}}\n"
        "⚡ Ресурсы в наличии: {pathogens}/{max_pathogens}\n"
        "⚙️ Уровень развития: {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Характеристики ]——\n"
        "🔥 Атака: {infect_lvl} ур\n"
        "🛡 Защита: {immunity_lvl} ур\n"
        "🔒 Блокировка: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "👁 Охрана: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Ресурсы ]——\n"
        "⚡ Опыт: {bio_experience}\n"
        "📦 Материалы: {bio_resource}\n"
        "⏰ Восстановление: Каждый день в 12.00 и 00.00</blockquote>"
        "🔒 Захвачено: {victims_count}\n"
        "📜 История: {illnesses_count}"
    )
    t["infect_success"] = (
        f"{infect_title}\n\n"
        f"Игрок {{attacker_mention}} успешно выполнил операцию против {{target_mention}}!\n"
        f"🎯 Использовано: <b>«{{pathogen_name}}»</b>\n\n"
        "📊 <b>Итог:</b>\n"
        "• Время удержания: <b>{fever_time}</b> мин.\n"
        "• Срок: <b>{expire_days}</b> дн.\n"
        "• Опыт: <b>+{exp_gain} EXP</b>\n\n"
        "✨ <i>Захвачено трофеев: +{res_gain}</i>"
    )
    t["infect_failed"] = (
        f"{fail_title}\n\n"
        "Защита объекта «{target_mention}» оказалась сильнее.\n"
        "Операция завершилась провалом.\n\n"
        "⚡ <b>Отчет:</b>\n"
        "• Остаток попыток: <b>{pathogens_left}</b>\n"
        "• Вероятность: <b>{penetration_chance}%</b>\n"
        "• Статус: <i>Провал.</i>"
    )
    t["infected_you"] = (
        "⚠️ <b>ВНИМАНИЕ!</b>\n\n"
        "Оператор {attacker_mention} применил к вам спец-протокол!\n\n"
        "🔒 Удержание: <b>{fever_time}</b> мин.\n"
        "⚙️ Срок действия: <b>{expire_days}</b> дн."
    )
    return t

THEMES_DATA = {
    "default": DEFAULT_THEME_DATA,
    "admin": ADMIN_THEME_DATA,
    "police": make_theme("🚨 Полицейский участок", "🚨 <b>Полицейский участок</b>", "Задержанный", "🏷 Ориентировка", "🚨 <b>ЗАДЕРЖАНИЕ ВЫПОЛНЕНО!</b>", "🛡 <b>ПОДОЗРЕВАЕМЫЙ СКРЫЛСЯ!</b>"),
    "it": make_theme("💻 IT-Серверная", "💻 <b>Серверный узел</b>", "Сервер", "🏷 Эксплойт", "💻 <b>ВЗЛОМ УСПЕШЕН!</b>", "🛡 <b>ФАЙРВОЛ ОТБИЛ АТАКУ!</b>"),
    "army": make_theme("🪖 Военная база", "🪖 <b>Военный гарнизон</b>", "Цель", "🏷 Приказ", "🪖 <b>ПРИКАЗ ВЫПОЛНЕН!</b>", "🛡 <b>ОБОРОНА ВЫСТОЯЛА!</b>"),
    "mafia": make_theme("🕶 Мафиозный клан", "🕶 <b>Синдикат</b>", "Должник", "🏷 Рэкет", "🕶 <b>КРЫШЕВАНИЕ УСТАНОВЛЕНО!</b>", "🛡 <b>ОТПОР ГАНГСТЕРАМ!</b>"),
    "zombie": make_theme("🧟 Бункер выживших", "🧟 <b>Убежище</b>", "Зараженный", "🏷 Штамм", "🧟 <b>ВИРУС РАСПРОСТРАНЕН!</b>", "🛡 <b>БУНКЕР ВЫДЕРЖАЛ!</b>"),
    "cyberpunk": make_theme("⚡ Киберпанк", "⚡ <b>Нейро-сеть</b>", "Субъект", "🏷 Имплант", "⚡ <b>НЕЙРО-ПЕРЕХВАТ УСПЕШЕН!</b>", "🛡 <b>НЕЙРО-ЩИТ СРАБОТАЛ!</b>"),
    "space": make_theme("🚀 Космостанция", "🚀 <b>Космостанция</b>", "Модуль", "🏷 Дрон", "🚀 <b>МОДУЛЬ ЗАХВАЧЕН!</b>", "🛡 <b>ЩИТЫ СТАНЦИИ ВЫДЕРЖАЛИ!</b>"),
    "fantasy": make_theme("🛡 Цитадель магии", "🛡 <b>Цитадель</b>", "Узник", "🏷 Заклинание", "🛡 <b>ПРОКЛЯТИЕ СРАБОТАЛО!</b>", "🛡 <b>МАГИЧЕСКИЙ БАРЬЕР ОТБИЛ АТАКУ!</b>"),
    "medic": make_theme("🏥 Госпиталь", "🏥 <b>Госпиталь</b>", "Пациент", "🏷 Диагноз", "🏥 <b>КАРАНТИН ВВЕДЕН!</b>", "🛡 <b>ИММУНИТЕТ СПАС ПАЦИЕНТА!</b>")
}

THEME_ID_MAP = {
    "default": 0,
    "admin": 100,
    "police": 1,
    "it": 2,
    "army": 3,
    "mafia": 4,
    "zombie": 5,
    "cyberpunk": 6,
    "space": 7,
    "fantasy": 8,
    "medic": 9,
    0: "default",
    100: "admin",
    1: "police",
    2: "it",
    3: "army",
    4: "mafia",
    5: "zombie",
    6: "cyberpunk",
    7: "space",
    8: "fantasy",
    9: "medic"
}

async def get_theme_text(db_or_theme, user_id_or_key=None, key_or_default="lab_dossier", default=""):
    if hasattr(db_or_theme, 'execute'):
        try:
            query = "SELECT active_theme FROM Users WHERE id = %s"
            await db_or_theme.execute(query, (user_id_or_key,))
            res = await db_or_theme.fetchone()
            theme_key = "default"
            if res:
                raw = res.get("active_theme") if isinstance(res, dict) else res[0]
                if str(raw) == "100" or str(raw).lower() == "admin":
                    theme_key = "admin"
                elif isinstance(raw, int) or (isinstance(raw, str) and raw.isdigit()):
                    theme_key = THEME_ID_MAP.get(int(raw), "default")
                elif raw:
                    theme_key = str(raw).lower()
            theme_data = THEMES_DATA.get(theme_key, DEFAULT_THEME_DATA)
            return theme_data.get(key_or_default, default)
        except Exception as e:
            print(f"[GET_THEME_TEXT ERROR] {e}")
            return DEFAULT_THEME_DATA.get(key_or_default, default)

    if isinstance(db_or_theme, str):
        theme_data = THEMES_DATA.get(db_or_theme, DEFAULT_THEME_DATA)
        return theme_data.get(user_id_or_key, default)

    return DEFAULT_THEME_DATA.get(key_or_default, default)

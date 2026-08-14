
ARMY_THEME_DATA = {
    "name": "🎖 Армейская",
    "lab_dossier": (
        "🎖 Военный бункер {lab_name}:\n"
        "Командир — {user_mention}\n"
        "{corp_name}\n\n"
        "🎯 Боевой приказ: {pathogen_name}\n"
        "💣 <b>Снаряды на складе:</b> {pathogens}/{max_pathogens}\n"
        "🪖 <b>Офицеры штаба:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Сводка Генштаба ]——\n"
        "⚔️ Убойная сила: {infect_lvl} ур\n"
        "🛡 Тяжелая броня: {immunity_lvl} ур\n"
        "⚡️ Гауптвахта: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🪂 Военная полиция: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "Личный номер: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Армейский Тыловой Склад ]——\n"
        "🎖 Боевой опыт: {bio_experience}\n"
        "📦 Снабжение: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>/n\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "🎖 {attacker_mention} отдал приказ на подавление {target_mention} по цели {pathogen_name} !\n☠️ Гауптвахта на {fever_time} минут\n🔒 В изоляции на {expire_days} дней\n🎯 +{exp_gain} боевого опыта",
    "infect_failed": "🛡 АТАКА ОТБИТА!\n\nОборона позиции {target_mention} выдержала натиск.\n\n💣 Осталось снарядов: {pathogens_left}\n📊 Шанс прорыва: {penetration_chance}%",
    "infected_you": "🎖 {attacker_mention} внес вас в черные списки гарнизона {target_mention}\n☠️ На гауптвахте на {fever_time} минут\n🔒 Ограничения на {expire_days} дней",
    "sb_report": "🪂 Военная полиция ({target_mention}) пресекла попытку диверсии от {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Цели под прицелом:</b>\n",
    "cases_menu": "📦 <b>Полевые ящики:</b>\n\n🪙 <b>Жалованье:</b> {epicoins}\n📦 <b>Армейский вещмешок:</b> {case1} шт.\n💎 <b>Офицерский сундук:</b> {case2} шт."
}

MAFIA_THEME_DATA = {
    "name": "🖤 Мафия",
    "lab_dossier": (
        "🖤 <b>Синдикат {lab_name}:</b>\n"
        "Дон — {user_mention}\n"
        "{corp_name}\n\n"
        "🔪 <b>Заказ:</b> {pathogen_name}\n"
        "💼 <b>Стволы в общаке:</b> {pathogens}/{max_pathogens}\n"
        "🕶 <b>Консильери:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Криминальная Сводка ]——\n"
        "🔥 Авторитет: {infect_lvl} ур\n"
        "🛡 Крыша: {immunity_lvl} ур\n"
        "⛓ Подвал: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🔫 Охрана «Семьи»: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID в синдикате: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Черный Общак ]——\n"
        "💵 Авторитет (опыт): {bio_experience}\n"
        "💎 Грязные деньги: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "🖤 {attacker_mention} передал «привет» от семьи для {target_mention} по делу {pathogen_name}!\n☠️ Заперт в подвале на {fever_time} минут\n⛓ Долговые обязательства на {expire_days} дней\n💵 +{exp_gain} авторитета",
    "infect_failed": "🛡 КРИШИ НЕ ПРОБИТЬ!\n\nВраги {target_mention} оказались сильнее вашего авторитета.\n\n💼 Осталось стволов: {pathogens_left}\n📊 Шанс наезда: {penetration_chance}%",
    "infected_you": "🖤 {attacker_mention} «заказал» ваш бизнес {target_mention}\n☠️ Проблемы на {fever_time} минут\n⛓ Под санкциями синдиката на {expire_days} дней",
    "sb_report": "🔫 Охрана синдиката ({target_mention}) перехватила засланного казачка {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Должники и объекты:</b>\n",
    "cases_menu": "📦 <b>Дипломаты с деньгами:</b>\n\n🪙 <b>Черный нал:</b> {epicoins}\n📦 <b>Чемоданчик:</b> {case1} шт.\n💎 <b>Сейф босса:</b> {case2} шт."
}

ZOMBIE_THEME_DATA = {
    "name": "🧟 Зомби",
    "lab_dossier": (
        "🧟 <b>Убежище выживших {lab_name}:</b>\n"
        "Вожак стаи — {user_mention}\n"
        "{corp_name}\n\n"
        "☣️ <b>Вирусный штамм:</b> {pathogen_name}\n"
        "🧪 <b>Запас заразы:</b> {pathogens}/{max_pathogens}\n"
        "🧬 <b>Мутаторы:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Статистика Заражения ]——\n"
        "🦠 Вирулентность: {infect_lvl} ур\n"
        "🛡 Плотный кокон: {immunity_lvl} ур\n"
        "🧠 Паралич нервной системы: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "👁 Сторожевые мутанты: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "Код выжившего: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Ресурсы Убежища ]——\n"
        "🧪 Мутаген (опыт): {bio_experience}\n"
        "🍖 Консервы/Биомасса: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "🧟 {attacker_mention} выпустил рой зомби на {target_mention} со штаммом {pathogen_name}!\n☠️ Паралич на {fever_time} минут\n🦠 Инкубация на {expire_days} дней\n🧪 +{exp_gain} мутагена",
    "infect_failed": "🛡 УКУС НЕ УДАЛСЯ!\n\nИммунитет {target_mention} оттолкнул орду.\n\n🧪 Осталось штамма: {pathogens_left}\n📊 Шанс укуса: {penetration_chance}%",
    "infected_you": "🧟 {attacker_mention} заразил ваше убежище штаммом {pathogen_name} {target_mention}\n☠️ Горячка на {fever_time} минут\n🦠 Инфекция на {expire_days} дней",
    "sb_report": "👁 Сторожевые мутанты ({target_mention}) зафиксировали лазутчика {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Заражённые особи:</b>\n",
    "cases_menu": "📦 <b>Контейнеры из лаборатории:</b>\n\n🪙 <b>Жетоны выживших:</b> {epicoins}\n📦 <b>Коробка с ампулами:</b> {case1} шт.\n💎 <b>Запечатанный бокс:</b> {case2} шт."
}

SPACE_THEME_DATA = {
    "name": "🚀 Космос",
    "lab_dossier": (
        "🚀 <b>Космическая станция {lab_name}:</b>\n"
        "Капитан — {user_mention}\n"
        "{corp_name}\n\n"
        "🛸 <b>Звездный маяк:</b> {pathogen_name}\n"
        "⚡️ <b>Заряды плазмы:</b> {pathogens}/{max_pathogens}\n"
        "👽 <b>Биоинженеры флота:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Бортовые Системы ]——\n"
        "☄️ Излучение: {infect_lvl} ур\n"
        "🛡 Энергощит: {immunity_lvl} ур\n"
        "🌀 Грави-ловушка: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🛰 Дрон-перехватчик: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID борта: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Трюм Корабля ]——\n"
        "✨ Космический опыт: {bio_experience}\n"
        "🔋 Темная материя: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "🚀 {attacker_mention} облучил сектор {target_mention} лучом {pathogen_name}!\n☠️ В грави-ловушке на {fever_time} минут\n🌀 Аномалия на {expire_days} дней\n✨ +{exp_gain} опыта",
    "infect_failed": "🛡 ЩИТЫ ВЫДЕРЖАЛИ!\n\nЭнергощит {target_mention} отразил космическую атаку.\n\n⚡️ Зарядов плазмы: {pathogens_left}\n📊 Шанс пробития щита: {penetration_chance}%",
    "infected_you": "🚀 {attacker_mention} захватил ваш шлюз сигналом {pathogen_name} {target_mention}\n☠️ Декомпрессия на {fever_time} минут\n🌀 Сбой систем на {expire_days} дней",
    "sb_report": "🛰 Дрон-перехватчик ({target_mention}) отбил атаку корабля {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Захваченные объекты:</b>\n",
    "cases_menu": "📦 <b>Грузовые контейнеры:</b>\n\n🪙 <b>Кредиты Альянса:</b> {epicoins}\n📦 <b>Стандартный модуль:</b> {case1} шт.\n💎 <b>Квантовый контейнер:</b> {case2} шт."
}

FANTASY_THEME_DATA = {
    "name": "🔮 Фэнтези",
    "lab_dossier": (
        "🔮 <b>Магическая цитадель {lab_name}:</b>\n"
        "Архимаг — {user_mention}\n"
        "{corp_name}\n\n"
        "📜 <b>Древнее заклятие:</b> {pathogen_name}\n"
        "✨ <b>Мана в резерве:</b> {pathogens}/{max_pathogens}\n"
        "🧙‍♂️ <b>Алхимики башни:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Магические Свойства ]——\n"
        "🪄 Сила чар: {infect_lvl} ур\n"
        "🛡 Защитный барьер: {immunity_lvl} ур\n"
        "💤 Проклятие сна: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "👁 Магический страж: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "Рунический код: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Алхимический Котел ]——\n"
        "🌟 Магический опыт: {bio_experience}\n"
        "🧪 Эссенция маны: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "🔮 {attacker_mention} наложил проклятие {pathogen_name} на {target_mention}!\n☠️ Глубокий сон на {fever_time} минут\n💤 Чары действуют {expire_days} дней\n🌟 +{exp_gain} опыта",
    "infect_failed": "🛡 МАГИЧЕСКИЙ ОТПОР!\n\nБарьер {target_mention} рассеял ваше заклинание.\n\n✨ Осталось маны: {pathogens_left}\n📊 Шанс проклятия: {penetration_chance}%",
    "infected_you": "🔮 {attacker_mention} околдовал вашу цитадель заклятием {pathogen_name} {target_mention}\n☠️ Оцепенение на {fever_time} минут\n💤 Проклятие на {expire_days} дней",
    "sb_report": "👁 Магический страж ({target_mention}) отразил колдовство мага {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Зачарованные объекты:</b>\n",
    "cases_menu": "📦 <b>Магические сундуки:</b>\n\n🪙 <b>Монеты царства:</b> {epicoins}\n📦 <b>Деревянный ларец:</b> {case1} шт.\n💎 <b>Рунический сундук:</b> {case2} шт."
}

MEDIC_THEME_DATA = {
    "name": "💊 Медицинская",
    "lab_dossier": (
        "🏥 <b>Медицинский центр {lab_name}:</b>\n"
        "Главврач — {user_mention}\n"
        "{corp_name}\n\n"
        "🔬 <b>Штамм-вирус:</b> {pathogen_name}\n"
        "💉 <b>Запас вакцин/шприцев:</b> {pathogens}/{max_pathogens}\n"
        "👩‍⚕️ <b>Инфекционисты:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Клинические Метрики ]——\n"
        "🦠 Контагиозность: {infect_lvl} ур\n"
        "🛡 Иммунитет: {immunity_lvl} ур\n"
        "🌡 Карантин: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🚨 Санитарная служба: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID врача: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Больничные Ресурсы ]——\n"
        "📋 Врачебный опыт: {bio_experience}\n"
        "🧪 Препараты: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "💊 {attacker_mention} инфицировал {target_mention} образцом {pathogen_name}!\n☠️ Карантин на {fever_time} минут\n🌡 Болезнь на {expire_days} дней\n📋 +{exp_gain} опыта",
    "infect_failed": "🛡 ИММУНИТЕТ СРАБОТАЛ!\n\nОрганизм {target_mention} отторг шприц-инъекцию.\n\n💉 Осталось шприцев: {pathogens_left}\n📊 Шанс заражения: {penetration_chance}%",
    "infected_you": "💊 {attacker_mention} назначил вам принудительный карантин {pathogen_name} {target_mention}\n☠️ В изоляторе на {fever_time} минут\n🌡 Лечение на {expire_days} дней",
    "sb_report": "🚨 Санитарная служба ({target_mention}) пресекла попытку заражения от {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Пациенты на карантине:</b>\n",
    "cases_menu": "📦 <b>Медицинские боксы:</b>\n\n🪙 <b>Премия Минздрава:</b> {epicoins}\n📦 <b>Кейс с ампулами:</b> {case1} шт.\n💎 <b>Элитный медпак:</b> {case2} шт."
}

# core/data/tricks/themes_data.py

THEME_ID_MAP = {
    0: "default",
    1: "police",
    2: "it",
    3: "army",
    4: "mafia",
    5: "zombie",
    6: "cyber",
    7: "space",
    8: "fantasy",
    9: "medic",
    10: "vip",
    11: "admin"
}

DEFAULT_THEME_DATA = {
    "name": "🧪 Обычная",
    "lab_dossier": (
        "📩<b> Досье лаборатории {lab_name}:</b>\n"
        "Руководитель — {user_mention}\n"
        "{corp_name}\n\n"
        "🏷 <b>Имя патогена:</b> {pathogen_name}\n"
        "🧪 <b>Патогены:</b> {pathogens}/{max_pathogens}\n"
        "🧑‍🎤<b>Учёные:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Статистика ]——\n"
        "💉 Заразность: {infect_lvl} ур\n"
        "🪬 Иммунитет: {immunity_lvl} ур\n"
        "💊 Летальность: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🕵️‍♂️ Служба безопасности: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "Ваш ID: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Запасы ]——\n"
        "☣️ Опыт: {bio_experience}\n"
        "🧬 Ресурсы: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "🦠 {attacker_mention} успешно заразил {target_mention} патогеном {pathogen_name}!\n☠️ Горячка на {fever_time} минут\n🤒 Заражение на {expire_days} дней\n☣️ +{exp_gain} опыта",
    "infect_failed": "🛡 ЗАРАЖЕНИЕ НЕ УДАЛОСЬ!\n\nИммунитет {target_mention} оказался сильнее вашего патогена.\n\n🧪 Осталось патогенов: {pathogens_left}\n📊 Шанс пробития был: {penetration_chance}%",
    "infected_you": "☣️ {attacker_mention} заразил вас патогеном  {pathogen_name} {target_mention}\n☠️ Горячка на {fever_time} минут\n🤒 Заражение на {expire_days} дней",
    "sb_report": "🕵️‍♂️ Ваша служба безопасности ({target_mention}) зафиксировала {attempts_count} попыток атаки!\nНападающий: {attacker_mention}",
    "victims_list_title": "🤒 <b>Ваши заражённые жертвы:</b>\n",
    "cases_menu": "📦 <b>Кейсы с патогенами:</b>\n\n🪙 <b>Эпикоины:</b> {epicoins}\n📦 <b>Обычный кейс:</b> {case1} шт.\n💎 <b>VIP кейс:</b> {case2} шт."
}

ADMIN_THEME_DATA = {
    "name": "👑 Админская",
    "lab_dossier": (
        "👑 <b>Корпоративный Сервер Мира {lab_name}:</b>\n"
        "Главный системный администратор — {user_mention}\n"
        "{corp_name}\n\n"
        "⚡️ <b>Основной эксплойт:</b> {pathogen_name}\n"
        "🔌 <b>Свободных ядер:</b> {pathogens}/{max_pathogens}\n"
        "💻 <b>Элитные разработчики:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Мониторинг Ядра ]——\n"
        "⚡️ Мощность атаки: {infect_lvl} ур\n"
        "🛡 Абсолютный файрвол: {immunity_lvl} ур\n"
        "☠️ Блокировка доступа: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🕵️‍♂️ Системный монитор: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "Root ID: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Ресурсы Системы ]——\n"
        "💎 Баланс опыта: {bio_experience}\n"
        "🔋 Серверные ресурсы: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "👑 Администратор {attacker_mention} применил системные санкции к {target_mention} штаммом {pathogen_name} !\n☠️ Блокировка на {fever_time} минут\n🔒 Изоляция на {expire_days} дней\n⚡️ +{exp_gain} опыта",
    "infect_failed": "🛡 СБОЙ АТАКИ!\n\nСистема защиты пользователя {target_mention} отразила административный запрос.\n\n⚡️ Осталось ядер: {pathogens_left}\n📊 Шанс пробития: {penetration_chance}%",
    "infected_you": "👑 Администратор {attacker_mention} заблокировал ваш узел патогеном {pathogen_name} {target_mention}\n☠️ Ограничения на {fever_time} минут\n🔒 Бан на {expire_days} дней",
    "sb_report": "🕵️‍♂️ Системный монитор ({target_mention}) зафиксировал попытку взлома от {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Заражённые объекты под наблюдением:</b>\n",
    "cases_menu": "📦 <b>Системные контейнеры:</b>\n\n🪙 <b>Эпикоины:</b> {epicoins}\n📦 <b>Админ-кейс:</b> {case1} шт.\n💎 <b>Root-кейс:</b> {case2} шт."
}

POLICE_THEME_DATA = {
    "name": "🚨 Полицейская",
    "lab_dossier": (
        "🚔 <b>Полицейский участок {lab_name}:</b>\n"
        "Шериф — {user_mention}\n"
        "{corp_name}\n\n"
        "📜 <b>Ориентировка:</b> {pathogen_name}\n"
        "📻 <b>Заряды спецсредств:</b> {pathogens}/{max_pathogens}\n"
        "👮‍♂️ <b>Детективы:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Сводка Уголовного Розыска ]——\n"
        "⚡️ Раскрываемость: {infect_lvl} ур\n"
        "🛡 Бронежилеты: {immunity_lvl} ур\n"
        "🚨 Срок заключения: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🚔 Спецназ (ОМОН): {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "Жетон: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Вещдоки и Награды ]——\n"
        "⭐ Выслуга лет: {bio_experience}\n"
        "📦 Протоколы: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "🚨 {attacker_mention} провел арест {target_mention} по статье {pathogen_name}!\n☠️ Изоляция на {fever_time} минут\n🔒 Срок заключения на {expire_days} дней\n⭐ +{exp_gain} выслуги лет",
    "infect_failed": "🛡 ПОПЫТКА АРЕСТА ПРОВАЛЕНА!\n\nПодозрительный {target_mention} скрылся от патруля.\n\n📻 Осталось спецсредств: {pathogens_left}\n📊 Шанс перехвата: {penetration_chance}%",
    "infected_you": "🚨 {attacker_mention} арестовал вас и поместил в изолятор {target_mention}\n☠️ В камере на {fever_time} минут\n🔒 Уголовный срок на {expire_days} дней",
    "sb_report": "🚔 Спецназ ({target_mention}) пресек попытку проникновения нарушителя {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Заражённые объекты:</b>\n",
    "cases_menu": "📦 <b>Конфискованные кейсы:</b>\n\n🪙 <b>Премия:</b> {epicoins}\n📦 <b>Стандартный сейф:</b> {case1} шт.\n💎 <b>Особый конфискат:</b> {case2} шт."
}

IT_THEME_DATA = {
    "name": "💻 IT / Хакерская",
    "lab_dossier": (
        "💻 <b>Хакерский дата-центр {lab_name}:</b>\n"
        "Тимлид — {user_mention}\n"
        "{corp_name}\n"
        "💾 <b>Эксплойт:</b> {pathogen_name}\n"
        "🔌 <b>Серверный поток:</b> {pathogens}/{max_pathogens}\n"
        "🧑‍💻 <b>Сеньор-разработчики:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Метрики Серверов ]——\n"
        "⚡️ Пропускная способность: {infect_lvl} ур\n"
        "🛡 Кибер-защита: {immunity_lvl} ур\n"
        "🔥 Нагрузка системы: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "👨‍💻 DevSecOps: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "IP сервера: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Хакерские Запасы ]——\n"
        "🔮 Пул опыта: {bio_experience}\n"
        "💾 Базы данных: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "💻 {attacker_mention} взломал сервер {target_mention} эксплойтом {pathogen_name}!\n☠️ Перегрузка CPU на {fever_time} минут\n💾 Блокировка доступа на {expire_days} дней\n🔮 +{exp_gain} к опыту",
    "infect_failed": "🛡 ВЗЛОМ ОТКЛОНЁН!\n\nФайрвол {target_mention} заблокировал ваш вредоносный пакет.\n\n🔌 Свободных потоков: {pathogens_left}\n📊 Шанс пробития защиты: {penetration_chance}%",
    "infected_you": "💻 {attacker_mention} занес троян в вашу систему {target_mention}\n☠️ Перегрузка на {fever_time} минут\n💾 Система заражена на {expire_days} дней",
    "sb_report": "👨‍💻 DevSecOps ({target_mention}) отразил кибератаку хакера {attacker_mention}! Попыток атаки: {attempts_count}",
    "victims_list_title": "🤒 <b>Заражённые объекты:</b>\n",
    "cases_menu": "📦 <b>Зашифрованные накопители:</b>\n\n🪙 <b>Крипто-валюта:</b> {epicoins}\n📦 <b>Базовый диск:</b> {case1} шт.\n💎 <b>Сверхбыстрый SSD:</b> {case2} шт."
}

CYBER_THEME_DATA = {
    "name": "⚡ Cyber",
    "lab_dossier": (
        "💻 <b>Сетевая Нео-Лаборатория {lab_name}:</b>\n"
        "Оператор — {user_mention}\n"
        "{corp_name}\n\n"
        "💾 <b>Био-код (патоген):</b> {pathogen_name}\n"
        "🔋 <b>Загружено эксплойтов:</b> {pathogens}/{max_pathogens}\n"
        "🤖 <b>Нейро-процессоры:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ CYBER METRICS ]——\n"
        "⚡ Заразность: {infect_lvl} ур\n"
        "🛡 Файрвол: {immunity_lvl} ур\n"
        "☣️ Летальность: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🥷 Кибер-защита: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID узла: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Системные Накопители ]——\n"
        "🔮 Опыт: {bio_experience}\n"
        "💾 Ресурсы: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "⚡ {attacker_mention} внедрил вирус-код в узел {target_mention} программатором {pathogen_name}!\n☠️ Перегрузка чипа на {fever_time} минут\n🔌 Сбой нейросети на {expire_days} дней\n🔮 +{exp_gain} единиц данных",
    "infect_failed": "🛡 СЕТЕВОЙ БАРЬЕР!\n\nКибер-защита {target_mention} заблокировала цифровой взлом.\n\n🔋 Зарядов эксплойта: {pathogens_left}\n📊 Шанс обхода защиты: {penetration_chance}%",
    "infected_you": "⚡ {attacker_mention} подсоединил вирус к вашему нейроинтерфейсу {target_mention}\n☠️ Сбой процессора на {fever_time} минут\n🔌 Инфекция ядра на {expire_days} дней",
    "sb_report": "🥷 Кибер-защита ({target_mention}) заблокировала сетевое внедрение от {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Заражённые объекты:</b>\n",
    "cases_menu": "📦 <b>Нейро-контейнеры:</b>\n\n🪙 <b>Кредиты:</b> {epicoins}\n📦 <b>Базовый чипсет:</b> {case1} шт.\n💎 <b>Квантовый накопитель:</b> {case2} шт."
}

VIP_THEME_DATA = {
    "name": "💎 VIP",
    "lab_dossier": (
        "🏛 <b>Досье VIP-комплекса {lab_name}:</b>\n"
        "Владелец — {user_mention}\n"
        "{corp_name}\n\n"
        "👑 <b>Премиум-патоген:</b> {pathogen_name}\n"
        "💎 <b>Запас ампул:</b> {pathogens}/{max_pathogens}\n"
        "🎩 <b>VIP-вирусологи:</b> {science_lvl} ур ({science_time} мин.)\n"
        "<i>{refresh_pathogen_time}</i>"
        "<blockquote>——[ Статус Систем ]——\n"
        "⚜️ Заразность: {infect_lvl} ур\n"
        "🛡 Иммунитет: {immunity_lvl} ур\n"
        "💎 Летальность: {fever_lvl} ур ({fever_time} мин | {expire_days} дн)\n"
        "🎩 Личная охрана: {sb_lvl} ур</blockquote>"
        "——————————————\n"
        "ID комплекса: <code>{user_id}</code>\n"
        "——————————————"
        "<blockquote>——[ Резерв VIP-ресурсов ]——\n"
        "✨ Опыт: {bio_experience}\n"
        "💎 Ресурсы: {bio_resource}\n"
        "⏱ <i>Получение бонусов: В 12.00 и 00.00</i></blockquote>\n"
        "🤒 Заражённых объектов: {victims_count}\n"
        "😷 Активных заражений: {illnesses_count}"
    ),
    "infect_success": "💎 {attacker_mention} поразил вип-элиту {target_mention} превосходным штаммом {pathogen_name}!\n☠️ Изоляция на {fever_time} минут\n💎 Статус инфицирован на {expire_days} дней\n✨ +{exp_gain} элитного опыта",
    "infect_failed": "🛡 VIP-БАРЬЕР!\n\nЭлитный иммунитет {target_mention} отразил заражение.\n\n💎 Запас VIP-ампул: {pathogens_left}\n📊 Шанс элитного заражения: {penetration_chance}%",
    "infected_you": "💎 {attacker_mention} заразил ваше VIP-убежище {pathogen_name} {target_mention}\n☠️ Недомогание на {fever_time} минут\n💎 Инфекция на {expire_days} дней",
    "sb_report": "🎩 Личная охрана ({target_mention}) пресекла проникновение от {attacker_mention}! Попыток: {attempts_count}",
    "victims_list_title": "🤒 <b>Заражённые объекты:</b>\n",
    "cases_menu": "📦 <b>Премиальные кейсы:</b>\n\n🪙 <b>Эпикоины:</b> {epicoins}\n📦 <b>Золотой кейс:</b> {case1} шт.\n💎 <b>Платиновый кейс:</b> {case2} шт."
}

THEMES_DATA = {
    "default": DEFAULT_THEME_DATA,
    "police": POLICE_THEME_DATA,
    "it": IT_THEME_DATA,
    "army": ARMY_THEME_DATA,
    "mafia": MAFIA_THEME_DATA,
    "zombie": ZOMBIE_THEME_DATA,
    "cyber": CYBER_THEME_DATA,
    "cyberpunk": CYBER_THEME_DATA,
    "space": SPACE_THEME_DATA,
    "fantasy": FANTASY_THEME_DATA,
    "medic": MEDIC_THEME_DATA,
    "vip": VIP_THEME_DATA,
    "admin": ADMIN_THEME_DATA,
}

async def get_theme_text(db_or_theme, user_id_or_key, text_key=None) -> str:
    from core.handlers.tricks.themes import get_user_theme
    
    if text_key is not None:
        theme_key = await get_user_theme(db_or_theme, user_id_or_key)
        key = text_key
    else:
        theme_key = db_or_theme
        key = user_id_or_key
        
    theme = THEMES_DATA.get(theme_key, DEFAULT_THEME_DATA)
    return theme.get(key, DEFAULT_THEME_DATA.get(key, ""))

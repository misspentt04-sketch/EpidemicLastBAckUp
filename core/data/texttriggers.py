from core.data.tricks.tricks_biowar import tricks_biowar

import re

re_pref = r'([!./]|)'
re_pref_ = r'[!./]'
re_pref_minus = r'([!./]|-|)'
refp = r'[!./]'
re_link_sup = r'(http(|s)://t\.me/|tg://openmessage\?user_id=|@)(\d{6,14}|[\w\d]{5,32})'


deep_links = {
    'tag': '@',
    'link': 'https://t.me/',
    'mention': 'tg://openmessage?user_id=',
    'mention_click': 'tg://user?id='
}

# Templates
# (лаб|лаба|лаборатория)
# [!._A-Za-zА-Яа-яё\d ] для имени лабы/патогена и тд.
# \s{1,3} spaces
# (|(\s+|)(\n.+|.+)) комментарий


### BioWar ###

# laboratory
re_lab = re.compile(re_pref + r'(лаб|лаба|моя (лаб|лаба|лаборатория))(| ' + re_link_sup + ')', re.IGNORECASE)
re_lab_lvlup_skills = re.compile(r'\+{1,2}(' + "|".join(tricks_biowar['lvlup_en_to_ru'].values()) + r')(| \d+)', re.IGNORECASE)
re_lab_biotop = re.compile(re_pref + r'(биотоп|бт)', re.IGNORECASE)
re_lab_biotop_chat = re.compile(re_pref + r'(биотоп (чата|беседы)|бч)', re.IGNORECASE)

# lab addons
re_change_lab_name = re.compile(r'[+!./]имя (лаб|лабы|лаборатория|лаборатории) [!._A-Za-zА-Яа-яё\d ]+', re.IGNORECASE)
re_remove_lab_name = re.compile(r'-имя (лаб|лабы|лаборатория|лаборатории)', re.IGNORECASE)
re_pathogen_name_change = re.compile(r'[+!./]имя патогена [!._A-Za-zА-Яа-яё\d ]+', re.IGNORECASE)
re_remove_pathogen_name = re.compile(r'-имя патогена', re.IGNORECASE)
re_lab_dossier = re.compile(r'(\+|-)(лаб|лаба|лаборатория)', re.IGNORECASE)
re_customization_emoji = re.compile(re_pref + r'(лаб|лаба|моя (лаб|лаба|лаборатория)) эмоджи [\w\d \S]{1,20}', re.IGNORECASE)
re_remove_customization_emoji = re.compile(re_pref_minus + r'(лаб|лаба|моя (лаб|лаба|лаборатория)) эмоджи', re.IGNORECASE)


# infect
re_infect = re.compile(
    re_pref +
    '('
    r'заразить\s{1,3}(|\d{1,2}\s{1,3})' + re_link_sup + '|'
    r'заразить\s{1,3}(-|=|\+|слаб(ее|ый|ого)|равн(ее|ый|ого)|сильн(ее|ый|ого)|рандом(|ный|ного))(|\s{1,3}\d{1,2})' +
    ')',
    re.IGNORECASE
)
re_infect_reply = re.compile(re_pref + r'заразить(|\s{1,3}\d{1,2})', re.IGNORECASE)
re_buy_vaccine = re.compile(re_pref + r'купить вакцину', re.IGNORECASE)
re_buy_vaccine_joke = re.compile(re_pref + r'курить вакцину', re.IGNORECASE)
re_victims_list = re.compile(re_pref + r'(мои жертвы|мж)', re.IGNORECASE)
re_illnesses_list = re.compile(re_pref + r'(мои болезни|мб)', re.IGNORECASE)

# Infect Addons
re_add_virus_signal = re.compile(r'\+вирусы', re.IGNORECASE)
re_del_virus_signal = re.compile(r'-вирусы', re.IGNORECASE)

# corporation
re_get_corporation = re.compile(re_pref + r'(моя|)(корпорация|корп)(| [a-z0-9]{1,6})', re.IGNORECASE)
re_create_corporation = re.compile(re_pref + r'корп создать [!._A-Za-zА-Яа-яё\d ]{1,48}', re.IGNORECASE)
re_invite_request_corporation = re.compile(r'\+корп [a-z0-9]{1,6}', re.IGNORECASE)
re_get_corporation_members = re.compile(re_pref + r'корп участники(| [a-z0-9]{1,6})', re.IGNORECASE)
re_get_corp_invites = re.compile(re_pref + r'корп заявки', re.IGNORECASE)
re_invite_accept_corporation = re.compile(re_pref + r'корп принять(| ' + re_link_sup + ')', re.IGNORECASE)
re_invite_reject_corporation = re.compile(re_pref + r'корп отказать(| ' + re_link_sup + ')', re.IGNORECASE)
re_delete_corporation = re.compile(re_pref + r'корп (удалить|ликвидировать)', re.IGNORECASE)
re_change_corporation_name = re.compile(re_pref + r'корп изменить [!._A-Za-zА-Яа-яё\d ]{,48}', re.IGNORECASE)
re_deladd_corporation_admin = re.compile(r'(\+|-)корп сорук(| ' + re_link_sup + ')', re.IGNORECASE)
re_get_corporation_admins = re.compile(re_pref + r'корп соруки', re.IGNORECASE)
re_corporation_dossier = re.compile(r'(\+|-)корп досье', re.IGNORECASE)
re_corporations_biotop = re.compile(re_pref + r'(биотоп корп|корп топ)', re.IGNORECASE)

re_kick_from_corporation = re.compile(re_pref + r'корп кик(| ' + re_link_sup + ')', re.IGNORECASE)
leave_corporation = re.compile(r'-корп', re.IGNORECASE)


# Pets
re_my_pet = re.compile(re_pref + r'(мой питомец|мой пет|мо[яй] (няшка|милая|очаровашка|любимая))', re.IGNORECASE)
re_my_pets = re.compile(re_pref + r'(мои питомцы|мои петы|мои (няшки|милашки|очаровашки|любимые))', re.IGNORECASE)
pet_the_pet = re.compile(re_pref + r'(погладить|гладить|ласкать)', re.IGNORECASE)

# Event
re_my_event_information = re.compile(re_pref + r'мой [иэе]вент', re.IGNORECASE)
re_event_biotop = re.compile(re_pref + r'(ивентоп|биотоп ивент(а|))', re.IGNORECASE)
re_event_character = re.compile(re_pref + r'мо(й|я) школьни(к|ца)', re.IGNORECASE)
re_event_backpack = re.compile(re_pref + r'мой рюкзак', re.IGNORECASE)
re_send_valentinka = re.compile(re_pref + r'(нефритка|открытка)(|\s\d{1,3})(|\s' + re_link_sup + ')' + r'(|(\s+|)(\n.+))', re.IGNORECASE)
re_send_gift = re.compile(re_pref + r'подарок(|\s' + re_link_sup + ')' + r'(|(\s+|)(\n.+))', re.IGNORECASE)

# Bag
get_bag = re.compile(re_pref + r'(ламинарий|ламинарный бокс|мой бокс|бокс)', re.IGNORECASE)
re_bag_send_currency = re.compile(re_pref + r'путешествие(|\s{1,3}\d+)(|\s{1,3}' + re_link_sup + r')(|(\s+|)(\n.+|.+))', re.IGNORECASE)

# Promo codes
re_promo_code_use = re.compile(re_pref + r'промо .{1,60}', re.IGNORECASE)
re_show_promo_codes = re.compile(re_pref + r'промолист', re.IGNORECASE)

# Krutki
re_krutka = re.compile(re_pref + r'крутка', re.IGNORECASE)
re_krutka_garant_choice = re.compile(re_pref + r'крутк(а|и) гарант', re.IGNORECASE)


# Admin commands
re_pathogen_mute = re.compile(re_pref + r'эпимут \d{1,4} ' + re_link_sup + r'(\s+|)(\n.+|.+)', re.IGNORECASE)
re_pathogen_mute_cancel = re.compile(r'-эпимут ' + re_link_sup, re.IGNORECASE)
re_game_mute = re.compile(re_pref + r'эпиас \d{1,4} ' + re_link_sup + r'(\s+|)(\n.+|.+)', re.IGNORECASE)
re_game_mute_cancel = re.compile(r'-эпиас ' + re_link_sup, re.IGNORECASE)
re_lab_transfer = re.compile(re_pref + r'эпилаб {} {}'.format(re_link_sup, re_link_sup), re.IGNORECASE)
re_check_gamemute = re.compile(re_pref + '!чек ' + re_link_sup, re.IGNORECASE)

# Triggers
re_funny_triggers = re.compile(r'(ирис|iris|ириска|биочмо|био-чмо|biochmo|bio-chmo)', re.IGNORECASE)

### Chat Managament ###

# Ping
re_ping = re.compile(re_pref + r'(бот|мяу|мур)', re.IGNORECASE)

# Notes
re_show_notes = re.compile(re_pref + r'заметки', re.IGNORECASE)
re_add_note = re.compile(re_pref + r'\+заметка .{1,64}(\n[\w\d\S\s]+)?', re.IGNORECASE)
re_show_note = re.compile(re_pref + r'заметка .{1,64}', re.IGNORECASE)
re_del_note = re.compile(re_pref + r'-заметка .{1,64}', re.IGNORECASE)

#IDS
re_get_id = re.compile(re_pref_ + r'(ид|id)(| ' + re_link_sup + ')', re.IGNORECASE)
re_check_chat_id = re.compile(re_pref_ + r'(чат ид|chat id)', re.IGNORECASE)

# Marriges
re_marry = re.compile(re_pref + r'(брак|пожениться|свадьба)(| ' + re_link_sup + ')', re.IGNORECASE)
re_marry_devorce = re.compile(re_pref + r'(развестись|развод|расторгнуть брак)(| ' + re_link_sup + ')', re.IGNORECASE)
re_show_marry = re.compile(re_pref + r'мой брак', re.IGNORECASE)
re_show_chat_marry = re.compile(re_pref + r'(браки|топ браков$)', re.IGNORECASE)
re_marry_restore = re.compile(re_pref + r'(восстановить брак|вернуть брак)(| ' + re_link_sup + ')', re.IGNORECASE)
re_marriage_comment = re.compile(re_pref + r'брак описание', re.IGNORECASE)

re_marriages_top_sms = re.compile(re_pref + r'(топ браков сообщения|топ браков смс)', re.IGNORECASE)
re_marriages_top_exp = re.compile(re_pref + r'(топ браков опыт|топ браков биоопыт)', re.IGNORECASE)

# Rules
re_add_rules = re.compile(r'\+правила(|\s{1,4})\n[\w\d\S\s]+', re.IGNORECASE)
re_get_rules = re.compile(re_pref + r'правила', re.IGNORECASE)
re_del_rules = re.compile(r'-правила', re.IGNORECASE)

# Admins
re_get_admins = re.compile(re_pref + r'кто админ|кто эпик', re.IGNORECASE)

# Chat Members
re_edit_greeting_on = re.compile(re_pref + r'\+приветствия|\-приветствия', re.IGNORECASE)
re_edit_leave_on = re.compile(re_pref + r'\+прощания|\-прощания', re.IGNORECASE)

# Shipper
re_ship = re.compile(re_pref + r'эпилав$|эпипара$', re.IGNORECASE)

# Help
re_help = re.compile(re_pref + r'(help|помощь)', re.IGNORECASE)

# User chat nickname
set_nickname = re.compile(re_pref + r'(ник|мой ник)\s{1,3}[!._A-Za-zА-Яа-яё\d ]{1,63}', re.IGNORECASE)

# Bot pm
re_bot_pm = re.compile(re_pref + r'эпилс(|.+)', re.IGNORECASE)

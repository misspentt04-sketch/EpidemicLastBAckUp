from core.data.texttriggers import deep_links
from core.data.icons import OtherIco, LabIco
from core.data.tricks.tricks_biowar import tricks_biowar
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage

from aiogram.methods.get_chat_administrators import GetChatAdministrators
from aiogram.types import ChatMemberAdministrator, ChatMemberMember
from aiogram.methods.get_chat_member import GetChatMember
from functools import lru_cache
from datetime import datetime
from typing import List
from humanize import intcomma
from aiogram.types import Message

from aiogram import Bot, html

from typing import Union, Literal
from asyncmy.cursors import Cursor

import asyncio
import re
import random
import string
import unicodedata
import subprocess
import json

@lru_cache()
def lvl_up_calc(skill, fromlvl: int, tolvl: int) -> int:

    price = 0
    
    for i in range(fromlvl, tolvl):
        if skill == 'pathogens':
            price += (i + 1) ** tricks_biowar['price']['skills']['pathogens']
        if skill == 'science':
            price += (i + 1) ** tricks_biowar['price']['skills']['science']
        if skill == 'infect':
            price += (i + 1) ** tricks_biowar['price']['skills']['infect']
        if skill == 'immunity':
            price += (i + 1) ** tricks_biowar['price']['skills']['immunity']
        if skill == 'lethality':
            price += (i + 1) ** tricks_biowar['price']['skills']['lethality']
        if skill == 'security_service':
            price += (i + 1) ** tricks_biowar['price']['skills']['security_service']
    
    return int(price)

def ping_link(user_id: int, text: str) -> str:
    return f'<a href="tg://user?id={user_id}">{text}</a>'

def link_getter(text: str) -> [str, bool]:
    expression = r'((http(|s)://t\.me/|@)[\w\d]{5,32}|tg://openmessage\?user_id=\d{6,14})'
    result = re.search(expression, text)
    if result:
        result = result[0].replace('https://t.me/', '').replace('tg://openmessage?user_id=', '').strip('@').replace('http://t.me/', '')
        if result.isdigit():
            return int(result)
        else:
            return str(result)
    else:
        return None

def entity_create_full_name(id: int, fname: str, lname: str=None, entity: str=deep_links['mention']) -> str:
    full_name = f'{fname} {lname}' if lname else fname
    return f'<a href="{entity}{id}">{full_name}</a>'

def entity_create(id: int | str, name: str, entity: str=deep_links['mention']) -> str:
    return f'<a href="{entity}{id}">{name}</a>'

def entity_create_consider_username(user: dict = None, user_id: int = None, name: str = None, username: str = None) -> str:
    if user:
        if user['username']:
            return entity_create(user['username'], user['full_name'], deep_links['link'])
        else:
            return entity_create(user['id'], user['full_name'])
    elif user_id and name:
        if username:
            return entity_create(username, name, deep_links['link'])
        else:
            return entity_create(user_id, name)
    else:
        raise SyntaxError('No provided any data')

async def entity_partners_create(partner1_id: int, partner2_id: int, repo_cm: RequestsRepoChatManage, repo_biowar: RequestsRepoBiowar):
    partner1 = await repo_biowar.get_info_user_lab(partner1_id)
    partner2 = await repo_biowar.get_info_user_lab(partner2_id)

    if not partner1 or not partner2:
        return {}, {} 

    partner1_entity = entity_create_full_name(partner1['id'], partner1['full_name'])
    partner2_entity = entity_create_full_name(partner2['id'], partner2['full_name'])

    return {'partner1_entity': partner1_entity}, {'partner2_entity': partner2_entity}


def get_full_name(fname: str, lname: str=None) -> str:
    return f'{fname} {lname}' if lname else fname

def strip_non_ascii(string) -> str:
    return ' '.join(re.findall(r'[\d\w\s]+', string))

def anti_specific_symbols_name(name: str, username: [str, bool], id: int) -> str:
    asci_name = strip_non_ascii(name)
    if asci_name != '':
        return asci_name
    elif username:
        return username
    else:
        return str(id)

def clear_name_universal(name: str, username: [str, bool], id: int) -> [int, str]:
    # re_pattern1 = r'[^\u0000-\u007F\u0080-\u00FF\u0100-\u017F\u0180-\u024F\u0370-\u03FF\u0400-\u04FF\u0500-\u052F]'
    re_pattern1 = re.compile(r'[^\u0000-\u007F\u00A0-\uFFFF]+')


    clear_name = anti_specific_symbols_name(
        html.quote(name), username, id
    )
    clear_name = re_pattern1.sub('', unicodedata.normalize('NFKC', clear_name))
    clear_name = re.sub(r'[^ -~А-Яа-яЁё]', '', clear_name)
    # clear_name = re.sub(re_pattern1, '', clear_name)
    # clear_name = ' '.join(clear_name.split())
    
    if re.fullmatch(r'[\s‎ ]+', clear_name) or not clear_name:
        clear_name = (username if username else id)
    
    return clear_name
    

def clear_tg_ban_words_name(name: str, ban_words: list):
    for i in ban_words:
        if i in name:
            name = name.replace(i, '')
    return name

def reply_or_tag_geeter(msg: Message):
    if [i for i in ['tg://openmessage?', '@', 'https://t.me/', 'http://t.me/'] if i in msg.text]:
        return link_getter(msg.text)
    else:
        return msg.reply_to_message.from_user.id if msg.reply_to_message else msg.from_user.id

def check_reply_or_tag(msg: Message):
    return [i for i in ['tg://openmessage?', '@', 'https://t.me/', 'http://t.me/'] if i in msg.text] or msg.reply_to_message

def check_if_tag(msg: Message):
    return [i for i in ['tg://openmessage?', '@', 'https://t.me/', 'http://t.me/'] if i in msg.text]

def convert_seconds(seconds: int):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return int(hours), int(minutes), int(seconds)

def convert_seconds_to_human(seconds_: int):
    hours, minutes, seconds = convert_seconds(seconds_)
    if hours:
        return f'{hours} часов {minutes} минут'
    elif not hours and minutes:
        return f'{minutes} минут'
    elif not hours and not minutes:
        return f'{seconds} секунд'

def diff_convert_timestamp_to_human(timestamp_time: int):
    now = datetime.utcnow()
    time = datetime.fromtimestamp(timestamp_time)
    dif = time - now
    difs = int(dif.total_seconds())
    hours, minutes, seconds = convert_seconds(difs)
    if difs > 0:
        if difs/60/60 >= 1:
            text = f'{hours} часов {minutes} минут'
        elif difs < 60:
            text = f'{seconds} секунд'
        else:
            text = f'{minutes} минут'
        return text
    else:
        return False

def victim_expire_difference_check(victim_time: int):
    now = datetime.utcnow()
    vic_time = datetime.fromtimestamp(victim_time)
    dif = vic_time - now
    difs = int(dif.total_seconds())
    hours, minutes, seconds = convert_seconds(difs)
    if difs > 0:
        if difs/60/60 >= 1:
            text = f'{hours} часов {minutes} минут'
        elif difs/60 >= 1:
            text = f'{minutes} минут'
        else:
            text = f'{seconds} секунд'
        return text
    else:
        return 'несколько секунд'

def fever_expire_difference_check(fever_seconds: int):
    now = datetime.utcnow()
    fever_time = datetime.fromtimestamp(fever_seconds)
    dif = fever_time - now
    difs = int(dif.total_seconds())
    hours, minutes, seconds = convert_seconds(difs)
    if difs > 0:
        if difs/60/60 >= 1:
            text = f'{hours} часов {minutes} минут {seconds} секунд'
        elif difs/60 >= 1:
            text = f'{minutes} минут {seconds} секунд'
        else:
            text = f'{seconds} секунд'
        return text
    else:
        return False

def corp_code_generator(length: int = 6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
def get_corp_members_or_invite_list(corp_members: List[dict], mode: ['members', 'invites']='members'):
    
    if not corp_members:
        return ''
    
    members_list = []
    
    member = 'member_id' if mode == 'members' else 'invite_user_id'
    
    for num, string in enumerate(corp_members, 1):
        members_list.append(
            (
                f'{num}. <a href="{deep_links["mention"]}{string[f"{member}"]}">{string["name"]}</a> | '
                f'{intcomma(string["bio_experience"])} опыт'
            )
        )
    
    return members_list

def get_corp_admins_list(corp_members: List[dict]):
    
    if not corp_members:
        return ''
    
    users_list = []
    
    for num, string in enumerate(corp_members, 1):
        users_list.append(
            (
                f'{num}. {OtherIco.star} <a href="{deep_links["mention"]}{string["member_id"]}">{string["name"]}</a>'
            )
        )
    
    return users_list

def get_biotop_corp(corp_members: List[dict]):
    
    if not corp_members:
        return ''
    
    users_list = []
    
    for num, string in enumerate(corp_members, 1):
        users_list.append(
            (
                f'{num}. <a href="{deep_links["mention"]}{string["leader_id"]}">{string["name"]}</a> | '
                f'{intcomma(string["bio_experience"])} опыт'
            )
        )
        if num >= 20:
            break
    
    return users_list

def get_biotop_lab(lab_list: List[dict]):
    
    if not lab_list:
        return ''
    
    users_list = [[], [0]]
    
    for num, string in enumerate(lab_list, 1):
        users_list[1][0] += string['bio_experience']
        users_list[0].append(
            (
                f'{num}. <a href="{deep_links["mention"]}{string["lab_id"]}">{string["lab_name"]}</a> | '
                f'{intcomma(string["bio_experience"])} опыт'
            )
        )
        if num >= 20:
            break
    
    return users_list

def get_notes_list(notes: List[dict]):
    
    if not notes:
        return ''
    
    note_list = []
    
    for string in notes:
        note_list.append(
            (
                f'{string["note_id"]}. {string["title"]}'
            )
        )
    
    return note_list

def get_victims_list(victims: List[dict]) -> list:
    
    victims_list = [[], [0]]
    
    if victims:
        for num, string in enumerate(victims, 1):
            to_date = datetime.fromtimestamp(string['victim_expire'])
            to_date_strf = datetime.strftime(to_date, '%d.%m.%Y')
            victims_list[1][0] += string['victim_bio_resource_earn']
            victims_list[0].append(
                (
                    f'{num}. <a href="{deep_links["mention"]}{string["victim_id"]}">{string["lab_name"]}</a> | '
                    f'+{intcomma(string["victim_bio_resource_earn"])} | до {to_date_strf}'
                )
            )
            if num >= 50:
                break
    
    if victims_list[0] == []:
        victims_list[0].append('\nУ вас пока нет жертв\n')
    
    return victims_list

def get_illness_list(illness: List[dict]):
    
    if not illness:
        return ''
    
    illness_list = []
    
    for num, string in enumerate(illness, 1):
        mention_link = f'<a href="{deep_links["mention"]}{string["victims_owner_id"]}">«{string["pathogen_name"]}»</a>'
        mention = (mention_link if string['ss_detect'] == 1 else string['pathogen_name'])
        to_date = datetime.fromtimestamp(string['victim_expire'])
        to_date_strf = datetime.strftime(to_date, '%d.%m.%Y')
        illness_list.append(
            (
                f'{num}. {mention} | до {to_date_strf}'
            )
        )
        if num >= 50:
            break
    
    return illness_list

def get_biotop_event(user_list: List[dict]):
    
    if not user_list:
        return ''
    
    biotop = []
    
    for num, string in enumerate(user_list, 1):
        biotop.append(
            (
                f'{num}. <a href="{deep_links["mention"]}{string["user_id"]}">{string["full_name"]}</a> '
                f'— Апрелек {string["aprelki"]} добыто ⏎'
            )
        )
        if num >= 25:
            break
    
    return biotop


async def get_admins_list(admin_chat_members: List[dict], chat_id: int):

    if not admin_chat_members:
        return '', 0  

    admins_list = [[], 0]  

    for index, admin_info in enumerate(admin_chat_members, 1):

        admin_info = format_admins_info(admin_info['admin_id'], admin_info, admin_info, index)
        admins_list[0].append(admin_info)
        admins_list[1] += 1

    return admins_list

def format_admins_info(admin_id, admin, admin_info, index):
    
    if not admin['admin_name']:
        name = 'админ'
    else:
        name = admin['admin_name']
    admin_entity = entity_create_full_name(admin_info['admin_id'], name)

    return f'{index}. <a href="{deep_links["mention"]}{admin_id}">{admin_entity}</a>'


async def devorce_marry(husband_id: int, wife_id: int, husband: str, wife: str):

    husband_entity = entity_create_full_name(husband_id, husband)
    wife_entity = entity_create_full_name(wife_id, wife)

    text = tricks_cm['marry']['last_devorce'].format(husband_entity, wife_entity)
    return text            

async def get_admins_chat(bot, chat_id):
    result: List[ChatMemberAdministrator] = await bot(GetChatAdministrators(chat_id=chat_id))
    return result

async def get_chat_members(bot, chat_id):
    result: Union[ChatMemberMember] = await bot(GetChatMember(chat_id=chat_id))


def show_backpack_part(backpack: dict, part: int):

    items = []
    avaliable_items = []
    lvl_price = 0
    
    for item, val in tricks_biowar['event']['backpack_items_en2ru'].items():
        items.append(item)
        if item in tricks_biowar['event']['backpack_items_part'][part]:
            avaliable_items.append(
                f'<tg-spoiler><s>{val}</s></tg-spoiler>'
                if backpack['current_item'] in items and
                item != backpack['current_item'] else f'{val} {backpack[item]}'
            )
    
    # stellar jade for lvlup
    if backpack['current_item'] in tricks_biowar['event']['backpack_items_part'][3]:
        lvl_price += int(backpack[backpack['current_item']]+1 ** 1.1)
    # primogem for lvlup
    else:
        lvl_price += int(backpack[backpack['current_item']]+1 ** 0.97)

    return avaliable_items, lvl_price

def which_event_item_part(item: str):
    if item in tricks_biowar['event']['backpack_items_part'][1]:
        return 1
    if item in tricks_biowar['event']['backpack_items_part'][2]:
        return 2
    if item in tricks_biowar['event']['backpack_items_part'][3]:
        return 3


async def get_biomute_list(repo_biowar: RequestsRepoBiowar, users: str):
    
    if not users:
        return ''
    
    users_list = []
    
    for num, string in enumerate(users, 1):
        mention_link = f'<a href="{deep_links["mention"]}{string["id"]}">«{string["full_name"]}»</a>'
        to_date = datetime.fromtimestamp(string['time_expire'])
        to_date_strf = datetime.strftime(to_date, '%d.%m.%Y %H:%M')
        admin = await repo_biowar.get_user(string['admin'])
        admin_mention = entity_create_consider_username(admin)
        users_list.append(
            (
                f'{num}. {mention_link} | до {to_date_strf} | выдан {admin_mention} | {string["reason"]}'
            )
        )
        if num >= 50:
            break
    
    return users_list

async def get_gamemute_list(repo_biowar: RequestsRepoBiowar, users: str):
    
    if not users:
        return ''
    
    users_list = []
    
    for num, string in enumerate(users, 1):
        mention_link = f'<a href="{deep_links["mention"]}{string["id"]}">«{string["full_name"]}»</a>'
        to_date = datetime.fromtimestamp(string['time_expire'])
        to_date_strf = datetime.strftime(to_date, '%d.%m.%Y %H:%M')
        admin = await repo_biowar.get_user(string['admin'])
        admin_mention = entity_create_consider_username(admin)
        users_list.append(
            (
                f'{num}. {mention_link} | до {to_date_strf} | выдан {admin_mention} | {string["reason"]}'
            )
        )
        if num >= 50:
            break
    
    return users_list

def go_get_top_marriage(chat_id: int, type: int):
    if type == 1:
        type_top = 'top_marriage'

    if type == 2:
        type_top = 'top_sms'
        
    if type == 3:
        type_top = 'top_exp'

    if type == 4:
        type_top = 'user_marriage'


    input_data = {
        "chat_id": chat_id,
        "type": type_top
    }

    input_json = json.dumps(input_data)

    go_binary_path = "./buster/go_buster"

    result = subprocess.run(
        [go_binary_path],
        input=input_json,  
        capture_output=True,
        text=True 
    )
    if result.returncode != 0:
        raise Exception(f"Go binary failed: {result.stderr}")

    return json.loads(result.stdout)

def go_get_user_marriage(chat_id: int, type: int, user_id: int):
    if type == 1:
        type_user = 'user_marriage'

    if type == 2:
        type_user = 'user_sms'
        
    if type == 3:
        type_user = 'user_exp'

    input_data = {
        "chat_id": chat_id,
        "type": type_user,
        "user_id": user_id
    }

    input_json = json.dumps(input_data)

    go_binary_path = "./buster/go_buster"

    result = subprocess.run(
        [go_binary_path],
        input=input_json,  
        capture_output=True,
        text=True 
    )
    if result.returncode != 0:
        raise Exception(f"Go binary failed: {result.stderr}")

    return json.loads(result.stdout)

def go_run_func(func: str):

    input_data = {
        "type": func
    }

    input_json = json.dumps(input_data)

    go_binary_path = "./buster/go_buster"

    result = subprocess.run(
        [go_binary_path],
        input=input_json,  
        capture_output=True,
        text=True 
    )
    if result.returncode != 0:
        raise Exception(f"Go binary failed: {result.stderr}")

    return json.loads(result.stdout)

def get_promo_list(promo: List[dict], promo_count: int):
    
    if not promo:
        return ''
    
    promo_list = []
    
    for num, string in enumerate(promo, 1):
        promo_type = string['type']
        if string['type'] == 'stellar_jade':
            promo_type = 'нефриты'
        if string['type'] == 'primogem':
            promo_type = 'примогемы'
        promo_list.append(
            (
                f'{num}. <code>{string["promo_code"]}</code> | тип {promo_type} | кол-во {string["val_count"]} | всего {promo_count}'
            )
        )
    
    return promo_list

def adjust_value(
    current_value: int | float, change: int | float, operator: Literal['-', '+'] = '+',
    max_lim: int = 100
    ) -> int | float:
    if operator == '+':
        new_value = current_value + change
    else:
        new_value = current_value - change
    
    if new_value > max_lim and max_lim != 0:
        return 100
    elif new_value < 0:
        return 0
    return new_value

def pet_current_happy_emoji(value: int) -> str:
    
    emoji = ['😖', '😞', '😔', '😐', '🙂', '☺️', '😊', '😇']
    values = [0, 15, 30, 45, 55, 65, 75, 85]

    for i in range(len(values) - 1):
        if value >= values[i] and value < values[i + 1]:
            return emoji[i]
        
    if value >= values[-1]:
        return emoji[-1]
    
    return emoji[0]
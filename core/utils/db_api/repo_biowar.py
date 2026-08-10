from asyncmy import Pool
from asyncmy.cursors import Cursor, DictCursor
from dataclasses import dataclass

from aiogram import types

from typing import Optional, Literal, Union, List

import asyncio

@dataclass
class RequestsRepoBiowar:
    cur: Cursor
    
    ### SQL Simple Queries ###
    
    async def select_all(self, sql: str, params: str = None, use_index_zero: bool = True):
        await self.cur.execute(sql, params)
        result = await self.cur.fetchall()
        if result:
            if use_index_zero:
                return result[0]
            else:
                return result
        else:
            return None
    
    async def select_one(self, sql: str, params: str = None):
        await self.cur.execute(sql, params)
        result = await self.cur.fetchone()
        if result:
            return result[list(result)[0]]
        else:
            return None
    
    ### Main Elements ###
    
    async def get_id_by_username(self, link: Union[int, str]):
        if str(link).isdigit():
            return link
        else:
            return await self.select_one('SELECT id FROM Users WHERE username=%s', link)
    
    async def get_user(self, link: Union[int, str]):
        column = 'id' if str(link).isdigit() else 'username'
        return await self.select_all('SELECT * FROM Users WHERE {}=%s'.format(column), link)
    
    ### Add main elements ###
    
    async def add_data_user(self, user_id: int, full_name: str, username: str = None):
        query = (
            'UPDATE Users SET username=NULL WHERE id!=%s AND username=%s;'
            'INSERT INTO Users (id, full_name, username) VALUES (%s, %s, %s) '
            'ON DUPLICATE KEY UPDATE'
            ' full_name=%s,'
            ' username=%s;'
        )
        params = (user_id, username, user_id, full_name, username, full_name, username)
        return await self.cur.execute(query, params)
    async def add_data_user_lower(self, user_id: int, full_name: str, username: str = None):
        query = (
            'UPDATE users SET username=NULL WHERE id!=%s AND username=%s;'
            'INSERT INTO users (id, full_name, username) VALUES (%s, %s, %s) '
            'ON DUPLICATE KEY UPDATE '
            'full_name=%s, '
            'username=%s;'
        )
        params = (user_id, username, user_id, full_name, username, full_name, username)
        return await self.cur.execute(query, params)
    
    async def add_data_chat(self, chat_id: int, title: str, user_id: int, is_private: bool):
        query = (
            'INSERT INTO Chat (chat_id, title, user_id, is_private) '
            'SELECT %s, %s, %s, %s FROM dual '
            'WHERE NOT EXISTS (SELECT 1 FROM Chat WHERE chat_id = %s AND user_id = %s)'
        )
        
        is_private_ = 1 if is_private else 0
        
        params = (chat_id, title, user_id, is_private_, chat_id, user_id)
        return await self.cur.execute(query, params)
    
    async def add_data_lab(self, user_id: int, full_name: str, lab_time_created: int):
        query = (
            'INSERT INTO Lab (lab_id, lab_name, lab_time_created, chat_setup_virus, bio_resource, bio_experience) '
            'SELECT %s, %s, %s, %s, %s, %s FROM dual'
            ' WHERE NOT EXISTS (SELECT 1 FROM Lab WHERE lab_id=%s);'
        )
    
        params = (user_id, full_name, lab_time_created, user_id, 15000, 1000, user_id)
        return await self.cur.execute(query, params)
    
    async def add_data_corp(self, user_id: int):
        query = (
            'INSERT IGNORE INTO Corporation'
            ' (leader_id, name, members, bio_experience, infected, invitation_code) VALUES'
            ' (%s, NULL, NULL, NULL, NULL, NULL);'
        )
        return await self.cur.execute(query, user_id)
    
    async def add_data_donate(self, user_id: int):
        query = (
            'INSERT INTO Donate (user_id)'
            'SELECT %s FROM dual'
            ' WHERE NOT EXISTS (SELECT 1 FROM Donate WHERE user_id=%s);'
        )
        return await self.cur.execute(query, (user_id, user_id))
    
    async def add_reputation_data(self, user_id: int):
        query = ("""
            INSERT INTO reputation (user_id)
            SELECT %s FROM dual
                WHERE NOT EXISTS (SELECT 1 FROM reputation WHERE user_id=%s);
        """)
        return await self.cur.execute(query, (user_id, user_id))

    async def add_event_backpack_data(self, user_id: int):
        query = ("""
            INSERT INTO event_backpack (user_id)
            SELECT %s FROM dual
                WHERE NOT EXISTS (SELECT 1 FROM event_backpack WHERE user_id=%s);
        """)
        return await self.cur.execute(query, (user_id, user_id))

    async def insert_user_last_message(self, user_id: int, event_update: types.Update):
        query = ("""
            INSERT INTO user_chat_messages (user_id, chat_id, last_message_id, last_message_text)
            VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE
                chat_id=%s,
                last_message_id=%s,
                last_message_text=%s;
        """)
        params = (
            user_id, event_update.message.chat.id, event_update.message.message_id,
            event_update.message.text, event_update.message.chat.id, event_update.message.message_id,
            event_update.message.text
        )
        await self.cur.execute(query, params)
    
    async def add_data_tutorial(self, user_id: int):
        query = 'INSERT IGNORE INTO tutorial (user_id) VALUES (%s);'
        await self.cur.execute(query, user_id)


    # User
    
    async def get_random_user(self):
        return await self.select_all('SELECT * FROM Users ORDER BY RAND() LIMIT 1;')

    ### Chat ###
    
    ## Update chat ##

    async def update_chat_title(self, chat_id: int, new_title: str):
        query = 'UPDATE Chat SET title=%s WHERE chat_id=%s;'
        await self.cur.execute(query, (new_title, chat_id))
    ## Get ##
    
    async def get_user_chat(self, user_id: int):
        query = 'SELECT * FROM Chat WHERE user_id = %s;'
        return await self.select_all(query, user_id)

    async def get_chat_by_id(self, chat_id: int):
        query = 'SELECT * FROM Chat WHERE chat_id = %s;'
        return await self.select_all(query, chat_id)
    
    async def get_chat_users_count(self, chat_id: int):
        return await self.select_one('SELECT COUNT(*) FROM Chat WHERE chat_id=%s;', chat_id)
    
    
    ### Lab ###
    
    ## Get ##
    
    async def get_info_user_lab(self, link: Union[int, str]):
        if str(link).isdigit():
            query = 'SELECT * FROM Users INNER JOIN Lab ON Lab.lab_id = id WHERE id=%s;'
            params = link
        else:
            user = await self.select_all('SELECT * FROM Users WHERE username = %s', link)
            if user:
                query = 'SELECT * FROM Users INNER JOIN Lab ON Lab.lab_id = id WHERE id=%s;'
                params = user['id']
            else:
                return None
        return await self.select_all(query, params)

    
    async def get_lab_biotop(self):
        query = 'SELECT * FROM Lab ORDER BY bio_experience DESC;'
        return await self.select_all(query, use_index_zero=False)
    
    async def get_lab_biotop_chat(self, chat_id: int):
        query = (
            'SELECT * FROM Lab INNER JOIN Chat ON Lab.lab_id = Chat.user_id '
            'WHERE chat_id=%s ORDER BY bio_experience DESC;'
        )
        return await self.select_all(query, chat_id, use_index_zero=False)

    async def get_corp_dossier(self, user_id: str=None, corp_code: int=None):
        column = 'invitation_code' if corp_code else 'leader_id'
        query = 'SELECT corporation_dossier FROM Corporation WHERE {}=%s;'.format(column)
        
        params = (corp_code if corp_code else user_id)
        return await self.select_one(query, params)
    
    async def get_my_infected(self, user_id: int):
        query = 'SELECT COUNT(victim_id) FROM Victims WHERE victims_owner_id=%s;'
        return await self.select_one(query, user_id)

    async def get_my_illnesses(self, user_id: int):
        query = 'SELECT COUNT(victim_id) FROM Victims WHERE victim_id=%s;'
        return await self.select_one(query, user_id)

    ## Update ##
    
    async def update_lab_lvlup(self, id: int, skill: str, skill_lvl: int, bio_resources: int):
        query = (
            'UPDATE Lab SET bio_resource=%s, {}=%s WHERE lab_id=%s;'.format(skill)
        )
        params = (bio_resources, skill_lvl, id)
        await self.cur.execute(query, params)
    
    async def update_lab_skill_val(self, id: int, skill: str, value: int):
        query = (
            'UPDATE Lab SET {}=%s WHERE lab_id=%s;'.format(skill)
        )
        params = (value, id)
        return await self.cur.execute(query, params)
    
    async def add_lab_bio_currency(self, id: int, bio_resources: int):
        query = 'UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s;'
        await self.cur.execute(query, (bio_resources, id))
        await self.conn.commit()

    async def add_epicoins(self, id: int, amount: int):
        query = 'UPDATE Lab SET epicoins = epicoins + %s WHERE lab_id = %s;'
        await self.cur.execute(query, (amount, id))
        await self.conn.commit()

    ### Lab Addons ###
    
    async def update_lab_dossier(self, dossier_val: int, id: int):
        query = 'UPDATE Lab SET lab_dossier=%s WHERE lab_id=%s;'
        return await self.cur.execute(query, (dossier_val, id))
    
    async def set_lab_customization_emoji(self, id: int, emoji: str):
        query = 'UPDATE Lab SET customization_emoji=%s WHERE lab_id=%s;'
        return await self.cur.execute(query, (emoji, id))
    
    # Update
    
    async def pathogen_name_change(self, pathogen_name: str, id: int):
        query = (
            'UPDATE Lab SET pathogen_name=%s WHERE lab_id=%s'
        )
        params = (pathogen_name, id)
        await self.cur.execute(query, params)
    
    async def lab_name_change(self, lab_name: str, id: int):
        return await self.cur.execute('UPDATE Lab SET lab_name=%s WHERE lab_id=%s;', (lab_name, id))
    
    ### Infections ###
    
    # Get
    
    async def get_victims(self, user_id: int):
        query = (
            'SELECT * FROM Victims INNER JOIN Lab ON lab_id=victim_id'
            ' WHERE victims_owner_id=%s ORDER BY infect_date DESC;'
        )
        return await self.select_all(query, user_id, use_index_zero=False)
    
    async def get_victim_by_infect_range(self, user_id: int, lower_val: int, higher_val: int):
        query = (
            'SELECT * FROM Users INNER JOIN Lab ON Lab.lab_id=Users.id '
            'WHERE lab_id != %s AND id != %s AND bio_experience BETWEEN %s AND %s ORDER BY RAND() LIMIT 1;'
        )
        params = (user_id, user_id, lower_val, higher_val)
        return await self.select_all(query, params)
    
    async def get_random_victim(self, user_id: int):
        query = (
            'SELECT * FROM Users INNER JOIN Lab ON Lab.lab_id=Users.id '
            'WHERE lab_id != %s AND id != %s ORDER BY RAND() LIMIT 1;'
        )
        params = (user_id, user_id)
        return await self.select_all(query, params)
    
    async def get_victims_food(self, user_id: int):
        query = 'SELECT SUM(victim_bio_resource_earn) FROM Victims WHERE victims_owner_id=%s;'
        return await self.select_one(query, user_id)
    
    # Update
    
    async def infect_setup(
        self, infecter_id: int, victim_id: int, earn_exp: int, vic_exp: int,
        victim_expire_kd: int, inf_pathogen: int,
        fever_seconds: int, vic_expire: int,
        infect_date: int, pathogen_name: str, ss_detect: int,
        science_time: int, is_science_time: bool, pet_boost_exp: int | bool):
        
        
        import datetime as dt_mod
        now_dt = dt_mod.datetime.now()
        week_s = now_dt.strftime('%G-%V')
        month_s = now_dt.strftime('%Y-%m')

        del_victims = 'DELETE FROM Victims WHERE victims_owner_id=%s AND victim_id=%s;'
        
        add_victims = (
            'INSERT INTO Victims (victims_owner_id, victim_id, victim_expire, infect_date,'
            ' victim_expire_kd, victim_bio_resource_earn, pathogen_name, ss_detect) VALUES '
            '(%s, %s, %s, %s, %s, %s, %s, %s) '
            'ON DUPLICATE KEY UPDATE '
            ' victim_id = %s,'
            ' victim_expire = %s,'
            ' infect_date = %s,'
            ' victim_expire_kd = %s,'
            ' victim_bio_resource_earn = %s,'
            ' pathogen_name = %s,'
            ' ss_detect = %s;'
        )

        add_exp = (
            'UPDATE Lab SET bio_experience=bio_experience+%s, ready_pathogens=%s WHERE lab_id=%s;'
            'UPDATE CorporationMembers SET bio_experience=bio_experience+%s WHERE member_id=%s;'
        )
        
        lost_exp = (
            'UPDATE Lab SET bio_experience=%s, fever=%s, fever_pathogen_name=%s WHERE lab_id=%s;'
            'UPDATE CorporationMembers SET bio_experience=%s WHERE member_id=%s;'
        )
        
        params1 = (
            infecter_id, victim_id, vic_expire, infect_date,
            victim_expire_kd, int(earn_exp+(pet_boost_exp if pet_boost_exp else 0)),
            pathogen_name, ss_detect, victim_id,
            vic_expire, infect_date, victim_expire_kd, earn_exp,
            pathogen_name, ss_detect
        )
        params2 = (
            earn_exp, inf_pathogen, infecter_id, earn_exp, infecter_id
        )
        params3 = (
            vic_exp, fever_seconds, pathogen_name, victim_id, vic_exp, victim_id
        )
        params4 = (infecter_id, victim_id)
        
        # Запись в историю заражений для топа
        add_history = "INSERT INTO biowar_infection_history (attacker_id, victim_id, week_str, month_str, infect_date) VALUES (%s, %s, %s, %s, NOW());"
        await self.cur.execute(add_history, (infecter_id, victim_id, week_s, month_s))
        await self.cur.execute(del_victims, params4)
        await self.cur.execute(add_victims, params1)
        await self.cur.execute(add_exp, params2)
        await self.cur.execute(lost_exp, params3)
        if not is_science_time:
            await self.update_lab_skill_val(infecter_id, 'science_time', science_time)
    
    async def subtract_pathogens(self, user_id: int, pathogens: int):
        query = 'UPDATE Lab SET ready_pathogens=GREATEST(0, ready_pathogens-%s) WHERE lab_id=%s;'
        await self.cur.execute(query, (pathogens, user_id))
    
    async def update_pet_boost_exp(self, user_id: int, pet_boost_exp: int):
        query = 'UPDATE Lab SET pet_boost_exp=%s WHERE lab_id=%s;'
        await self.cur.execute(query, (pet_boost_exp, user_id))

    ## Check ##
    
    async def check_victim_expire(self, owner_victim_id, victim_id: int) -> Union[str, bool]:
        request = await self.select_one(
            'SELECT victim_expire_kd FROM Victims WHERE victims_owner_id = %s AND victim_id = %s;',
            (owner_victim_id, victim_id)
        )
        if request:
            return request
        else:
            return False


    ### Infections Addons ###
    
    # Get
    
    async def get_illnesses(self, user_id: int):
        query = (
            'SELECT * FROM Victims INNER JOIN Lab ON lab_id=victim_id'
            ' WHERE victim_id=%s ORDER BY infect_date DESC;'
        )
        return await self.select_all(query, user_id, use_index_zero=False)
    
    # Update
    
    async def buy_vaccine(self, bio_resource: int, victim_id: int):
        query = 'UPDATE Lab SET fever=NULL, bio_resource=bio_resource-%s WHERE lab_id=%s;'
        params = (bio_resource, victim_id)
        await self.cur.execute(query, params)

    async def buy_vaccine_epicoins(self, epicoins: int, victim_id: int):
        query = 'UPDATE Lab SET fever=NULL, epicoins=epicoins-%s WHERE lab_id=%s AND epicoins>=%s;'
        params = (epicoins, victim_id, epicoins)
        await self.cur.execute(query, params)
        if hasattr(self.cur, "connection") and self.cur.connection:
            await self.cur.connection.commit()
    
    async def update_virus_chat_setup(self, user_id: int, chat_id: int):
        query = 'UPDATE Lab SET chat_setup_virus=%s WHERE lab_id=%s;'
        await self.cur.execute(query, (chat_id, user_id))
    
    async def del_virus_chat_setup(self, user_id: int):
        query = 'UPDATE Lab SET chat_setup_virus=NULL WHERE lab_id=%s;'
        await self.cur.execute(query, user_id)

    
    ### Corporation ###
    
    # Get
    
    async def get_corporation(self, user_id: int=None, corp_code: str=None):
        column = 'corporation_code' if corp_code else 'member_id'
        query = (
            'SELECT * FROM Corporation INNER JOIN CorporationMembers '
            'ON CorporationMembers.corporation_code = invitation_code WHERE {}=%s;'.format(column)
        )
        
        return await self.select_all(query, corp_code if corp_code else user_id)
    
    async def get_biotop_corps(self):
        query = 'SELECT * FROM Corporation ORDER BY bio_experience DESC;'
        return await self.select_all(query, use_index_zero=False)
    
    async def get_corporation_members(self, corp_code: str):
        query = 'SELECT * FROM CorporationMembers WHERE corporation_code=%s ORDER BY bio_experience DESC;'
        return await self.select_all(query, corp_code, False)
    
    async def get_corporation_members_ids_list(self, corp_code: str):
        query = 'SELECT * FROM CorporationMembers WHERE corporation_code=%s ORDER BY bio_experience DESC;'
        members = await self.select_all(query, corp_code, False)
        return [id['member_id'] for id in members]
    
    async def get_corporation_members_count(self, corp_code: str):
        query = 'SELECT COUNT(member_id) FROM CorporationMembers WHERE corporation_code=%s;'
        return await self.select_one(query, corp_code)
    
    async def get_corp_invite_list(self, corp_code: str):
        query = 'SELECT * FROM CorporationInviteList WHERE corporation_code=%s ORDER BY bio_experience DESC;'
        return await self.select_all(query, corp_code, False)
    
    async def get_corp_admin_list(self, corp_code: str):
        query = 'SELECT * FROM CorporationMembers WHERE corporation_code=%s AND is_admin=1;'
        return await self.select_all(query, corp_code, False)
    
    ## create ##
    
    async def create_corporation(
        self, owner_id: int, corp_name: str, name: str,
        exp: int, infected: int, invite_code: str):
        query = (
            'INSERT INTO Corporation'
            ' (leader_id, name, members, bio_experience, infected, invitation_code) VALUES'
            ' (%s, %s, %s, %s, %s, %s);'
        )
        
        query1 = (
            'INSERT INTO CorporationMembers'
            ' (corporation_code, member_id, name, bio_experience, infected, is_admin) VALUES'
            ' (%s, %s, %s, %s, %s, %s);'
        )
        
        params = (owner_id, corp_name, 1, exp, infected, invite_code)
        params1 = (invite_code, owner_id, name, exp, infected, 1)
        await self.cur.execute(query, params)
        await self.cur.execute(query1, params1)
    
    ## Update ##
    
    async def update_corp_admin(self, admin_id: int, corp_code: str, is_admin: int):
        query = 'UPDATE CorporationMembers SET is_admin=%s WHERE corporation_code=%s AND member_id=%s;'
        params = (is_admin, corp_code, admin_id)
        await self.cur.execute(query, params)
    
    async def update_corp_dossier(self, corp_code: str, dossier: str):
        query = 'UPDATE Corporation SET corporation_dossier=%s WHERE invitation_code=%s;'
        params = (dossier, corp_code)
        await self.cur.execute(query, params)
    
    ## Check ##
    
    async def check_if_owner_corporation(self, corp_code: str, user_id: int) -> bool:
        query = (
            'SELECT leader_id FROM Corporation WHERE leader_id=%s AND invitation_code=%s;'
        )
        params = (user_id, corp_code)
        return await self.select_one(query, params)
    
    async def corp_check_invite_request(self, invite_user_id: int, corp_code: str):
        query = 'SELECT invite_user_id FROM CorporationInviteList WHERE invite_user_id=%s AND corporation_code=%s;'
        params = (invite_user_id, corp_code)
        return await self.select_one(query, params)
    
    ## Others ##

    async def delete_corporation(self, corp_code: int):
        query = (
            'DELETE FROM CorporationMembers WHERE corporation_code = %s;'
            'DELETE FROM CorporationInviteList WHERE corporation_code = %s;'
            'DELETE FROM Corporation WHERE invitation_code = %s;'
        )
        
        params = (corp_code, corp_code, corp_code)
        
        await self.cur.execute(query, params)
    
    async def leave_corporation(self, corp_code: str, user_id: int):
        query = (
            'DELETE FROM CorporationMembers WHERE corporation_code=%s AND member_id=%s;'
            'UPDATE Corporation SET members=members-1 WHERE invitation_code=%s;'
        )
        
        params = (corp_code, user_id, corp_code)
        
        await self.cur.execute(query, params)
    
    async def change_corp_name(self, corp_code: str, name: str):
        query = 'UPDATE Corporation SET name=%s WHERE invitation_code=%s;'
        
        params = (name, corp_code)
        await self.cur.execute(query, params)
    
    async def send_invite_request_corporation(self, corp_code: int, user_id: int, name: str, exp: int):
        query = (
            'INSERT INTO CorporationInviteList'
            ' (invite_user_id, corporation_code, name, bio_experience) VALUES'
            ' (%s, %s, %s, %s)'
        )
        
        params = (user_id, corp_code, name, exp)
        
        await self.cur.execute(query, params)
    
    async def claim_invite_request_corporation(self, corp_code: int, user_id: int, name: str, exp: int, infected: int):
        query = (
            'INSERT INTO CorporationMembers'
            ' (corporation_code, member_id, name, bio_experience, infected) VALUES'
            ' (%s, %s, %s, %s, %s);'
        )
        
        query1 = (
            'DELETE FROM CorporationInviteList WHERE invite_user_id=%s'
        )
        
        query2 = (
            'UPDATE Corporation SET members=members+1 WHERE invitation_code=%s;'
        )
        
        params = (corp_code, user_id, name, exp, infected)
        params1 = (user_id)
        params2 = (corp_code)
        
        await self.cur.execute(query, params)
        await self.cur.execute(query1, params1)
        await self.cur.execute(query2, params2)
    
    async def reject_invite_request_corporation(self, corp_code: int, user_id: int):
        query = (
            'DELETE FROM CorporationInviteList WHERE invite_user_id=%s AND corporation_code=%s'
        )
        
        params = (user_id, corp_code)
        
        await self.cur.execute(query, params) 
    
    # Event
    
    async def add_event_user_info(self, user_id: int):
        query = (
            'INSERT INTO Event (id, pathogens_used, infected) '
            'SELECT %s, %s, %s FROM dual'
            ' WHERE NOT EXISTS (SELECT 1 FROM Event WHERE id=%s);'
        )
        params = (user_id, 0, 0, user_id)
        await self.cur.execute(query, params)
    
    async def get_event_biotop(self):
        query = 'SELECT * FROM event_aprelki INNER JOIN Users ON event_aprelki.user_id=Users.id ORDER BY aprelki DESC;'
        biotop = await self.select_all(query, use_index_zero=False)
        
        return biotop
    
    async def create_valentinka_column(self, user_id: int):
        query = ("""
            INSERT IGNORE INTO event_valentin (user_id, valentin_have_count) VALUES (%s, 0);
        """)
        await self.cur.execute(query, user_id)
    
    async def send_valentinka(self, user_id: int, gift_to_user_id: int, count_valentin: int):
        query = ("""
            INSERT INTO event_valentin (user_id, valentin_have_count) VALUES (%s, %s) ON DUPLICATE KEY UPDATE
             valentin_have_count=valentin_have_count+%s;
        """)
        params = (gift_to_user_id, count_valentin, count_valentin)
        await self.cur.execute(query, params)
        query = 'UPDATE event_valentin SET valentin_gift_count=valentin_gift_count+%s WHERE user_id=%s;'
        params = (count_valentin, user_id)
        await self.cur.execute(query, params)
    
    async def update_epilove_count(self, user_id: int):
        await self.cur.execute('UPDATE event_valentin SET epilove_use_count=epilove_use_count+1 WHERE user_id=%s', user_id)
    
    async def event_get_character(self, user_id: int):
        query = 'SELECT * FROM event_character WHERE user_id=%s;'
        return await self.select_all(query, user_id)

    async def event_create_character(self, user_id: int, gender: str):
        query = 'INSERT INTO event_character (user_id, lvl, gender) VALUES (%s, 1, %s)'
        await self.cur.execute(query, (user_id, gender))

    async def event_update_character_lvl(self, user_id: int):
        query = 'UPDATE event_character SET lvl=lvl+1 WHERE user_id=%s;'
        await self.cur.execute(query, user_id)

    async def get_event_backpack(self, user_id: int):
        query = 'SELECT * FROM event_backpack WHERE user_id=%s;'
        return await self.select_all(query, user_id)

    async def event_add_percent_item(self, user_id: int):
        query = 'UPDATE event_backpack SET percent_to_new_item=percent_to_new_item+1.5 WHERE user_id=%s;'
        return await self.cur.execute(query, user_id)

    async def event_finish_item_action(self, user_id: int, new_item: str):
        query = 'UPDATE event_backpack SET percent_to_new_item=0, current_item="{}" WHERE user_id=%s;'.format(new_item)
        await self.cur.execute(query, user_id)
        query = 'UPDATE event_backpack SET {}=1 WHERE user_id=%s;'.format(new_item)
        await self.cur.execute(query, user_id)

    async def event_update_item_lvl(self, user_id: int, item: str):
        query = 'UPDATE event_backpack SET {}={}+1 WHERE user_id=%s;'.format(item, item)
        await self.cur.execute(query, user_id)

    async def get_my_aprelki(self, user_id: int):
        query = 'SELECT * FROM event_aprelki WHERE user_id=%s;'
        return await self.select_all(query, user_id)
    
    async def setup_my_aprelki(self, user_id: int, aprelki: int, next_time: int):
        query = 'UPDATE event_aprelki SET aprelki=%s, aprelki_next_time=%s WHERE user_id=%s;'
        await self.cur.execute(query, (aprelki, next_time, user_id))

    async def add_my_aprelki(self, user_id: int):
        await self.cur.execute('INSERT IGNORE INTO event_aprelki (user_id) VALUES (%s);', user_id)

    # Bag
    
    async def add_bag(self, user_id: int):
        query = (
            'INSERT INTO Bag (id, primogem, stellar_Jade) '
            'SELECT %s, %s, %s FROM dual'
            ' WHERE NOT EXISTS (SELECT 1 FROM Bag WHERE id=%s);'
        )
        params = (user_id, 0, 0, user_id)
        await self.cur.execute(query, params)

    async def get_bag(self, user_id: int):

        query = 'SELECT * FROM Bag WHERE id = %s'
        params = (user_id)

        return await self.select_all(query, params)
    
    # update
    
    async def update_bag_primogem(self, user_id: int, primogem: int, operator: Literal['+', '-', None] = '+'):
        if operator is None:
            return await self.cur.execute(
                'UPDATE Bag SET primogem=%s WHERE id=%s', (primogem, user_id)
            )
        await self.cur.execute('UPDATE Bag SET primogem=primogem{}%s WHERE id=%s'.format(operator), (primogem, user_id))
    
    async def update_bag_stellar_jade(self, user_id: int, stellar_jade: int, operator: Literal['+', '-', None] = '+'):
        if operator is None:
            return await self.cur.execute(
                'UPDATE Bag SET stellar_jade=%s WHERE id=%s', (stellar_jade, user_id)
            )
        await self.cur.execute(
            'UPDATE Bag SET stellar_jade=stellar_jade{}%s WHERE id=%s'.format(operator), (stellar_jade, user_id)
        )
    
    # Pets
    
    # get
    async def get_my_pet(self, user_id: int):
        return await self.select_all(
            'SELECT * FROM Pets WHERE owner_pet_id=%s AND pet_name=(SELECT current_pet FROM Pets WHERE owner_pet_id=%s LIMIT 1);',
            (user_id, user_id)
        )
    
    async def get_my_pets(self, user_id: int):
        return await self.select_all('SELECT * FROM Pets WHERE owner_pet_id=%s;', user_id, use_index_zero=False)

    # update
    async def setup_pet_the_pet(self, user_id: int, pet_the_pet_time: int, pet_happy_percent: int):
        query = 'UPDATE Pets SET pet_the_pet_time=%s, happy=%s WHERE owner_pet_id=%s;'
        params = (pet_the_pet_time, pet_happy_percent, user_id)
        await self.cur.execute(query, params)
    
    async def give_pet(
        self,
        user_id: int,
        pet_name: str,
        element: str,
    ):
        query = (
            'INSERT INTO Pets (owner_pet_id, pet_name, element) '
            'VALUES (%s, %s, %s);'
        )
        params = (user_id, pet_name, element)
        await self.cur.execute(query, params)
    
    async def change_current_pet(self, user_id: int, pet: str):
        await self.cur.execute('UPDATE Pets SET current_pet="{}" WHERE owner_pet_id=%s;'.format(pet), user_id)
    
    # Donate
    
    async def get_user_donate(self, user_id: int):
        return await self.select_all('SELECT * FROM Donate WHERE user_id=%s', user_id)
    
    async def change_kit_donate(self, user_id: int, kit_id: int, value: int):
        await self.cur.execute('UPDATE Donate SET kit{}={} WHERE user_id=%s'.format(kit_id, value), user_id)
    
    # Promocodes
    
    async def get_promocode(self, promo_code: str):
        return await self.select_all('SELECT * FROM promo_code WHERE promo_code=%s;', promo_code)
    
    async def delete_promo(self, promo_id: int):
        await self.cur.execute('DELETE FROM promo_code WHERE id=%s;', promo_id)
    
    async def show_promocodes(self):
        promo_codes = await self.select_all('SELECT DISTINCT promo_code, type, val_count FROM promo_code;', use_index_zero=False)
        promo_count = await self.select_one('SELECT COUNT(*) FROM promo_code;')
        return promo_count, promo_codes
    
    async def user_add_promo_usage(self, user_id: int, promo_code: str):
        await self.cur.execute(
            'INSERT IGNORE INTO promo_code_user (user_id, promo_code) VALUES (%s, %s);',
            (user_id, promo_code)
        )
    
    async def get_user_promo(self, user_id: int, promo_code: str):
        return await self.select_all(
            'SELECT * FROM promo_code_user WHERE user_id=%s AND promo_code=%s;',
            (user_id, promo_code)
        )
    
    # Admin

    async def bio_mute(self, user_id: int, lab_name: str, corp: dict, time_expire: int, admin_id: int, reason: str):


        query = (


            'INSERT INTO BioMute (user_id, time_expire, admin, reason) VALUES (%s, %s, %s, %s)'


            ' ON DUPLICATE KEY UPDATE'


            ' time_expire=%s,'


            ' admin=%s,'


            ' reason=%s;'


        )



        query_del_game_names = """


        UPDATE Lab SET pathogen_name=NULL WHERE lab_id=%s;


        UPDATE Lab SET lab_name=NULL WHERE lab_id=%s;


        """



        params = (user_id, time_expire, admin_id, reason, time_expire, admin_id, reason)


        params1 = (user_id, user_id)


        await self.cur.execute(query, params)


        await self.cur.execute(query_del_game_names, params1)



    async def bio_mute_cancel(self, user_id: int):
        query = 'DELETE FROM BioMute WHERE user_id=%s;'
        
        await self.cur.execute(query, user_id)

    async def get_user_bio_mute(self, user_id):
        query = 'SELECT * FROM BioMute WHERE user_id=%s;'
        return await self.select_all(query, user_id)
    
    async def game_mute(self, user_id: int, time_expire: int, admin_id: int, reason: str):
        query = (
            'INSERT INTO GameMute (user_id, time_expire, admin, reason) VALUES (%s, %s, %s, %s)'
            ' ON DUPLICATE KEY UPDATE'
            ' time_expire=%s,'
            ' admin=%s,'
            ' reason=%s;'
        )
        
        params = (user_id, time_expire, admin_id, reason, time_expire, admin_id, reason)
        await self.cur.execute(query, params)

    async def game_mute_cancel(self, user_id: int):
        query = 'DELETE FROM GameMute WHERE user_id=%s;'
        
        await self.cur.execute(query, user_id)

    async def get_user_game_mute(self, user_id: int):
        query = 'SELECT * FROM GameMute WHERE user_id=%s;'
        return await self.select_all(query, user_id)
    
    async def get_biomute_list(self):
        query = 'SELECT bm.*, u.full_name, u.username FROM BioMute AS bm LEFT JOIN Users AS u ON bm.user_id = u.id;'
        return await self.select_all(query, use_index_zero=False)

    async def get_gamemute_list(self):
        query = 'SELECT gm.*, u.full_name, u.username FROM GameMute AS gm LEFT JOIN Users AS u ON gm.user_id = u.id;'
        return await self.select_all(query, use_index_zero=False)

    async def lab_tranfer(self, lab_from: dict, lab_to: dict, bag_from: dict, bag_to: dict, pet_from: dict):
        source_id = lab_from.get('id') or lab_from.get('lab_id') if isinstance(lab_from, dict) else lab_from
        target_id = lab_to.get('id') or lab_to.get('lab_id') if isinstance(lab_to, dict) else lab_to

        queries = [
            ("SET FOREIGN_KEY_CHECKS = 0;", ()),
            ("DELETE FROM Lab WHERE lab_id = %s;", (target_id,)),
            ("DELETE FROM Bag WHERE id = %s;", (target_id,)),
            ("DELETE FROM Victims WHERE victims_owner_id = %s;", (target_id,)),
            ("UPDATE Lab SET lab_id = %s WHERE lab_id = %s;", (target_id, source_id)),
            ("UPDATE Bag SET id = %s WHERE id = %s;", (target_id, source_id)),
            ("UPDATE IGNORE Victims SET victims_owner_id = %s WHERE victims_owner_id = %s;", (target_id, source_id)),
            ("SET FOREIGN_KEY_CHECKS = 1;", ())
        ]
        for q, p in queries:
            if p:
                await self.cur.execute(q, p)
            else:
                await self.cur.execute(q)

# Suggestions #

    async def add_suggestion(self, user_id: int, category: str, text: str):
        query = (
            "INSERT INTO suggestions "
            "(user_id, category, text) "
            "VALUES (%s, %s, %s);"
        )
        return await self.cur.execute(query, (user_id, category, text))

    async def get_suggestions(self):
        return await self.select_all(
            "SELECT * FROM suggestions ORDER BY id DESC;"
        )

    # Service #

    async def get_time_food(self):
        return await self.select_one(
            "SELECT time_give_food FROM Service;"
        )

    async def update_admin_last_seen(self, user_id: int, timestamp: int):
        query = (
            "INSERT INTO admin_status (user_id, last_seen) "
            "VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE last_seen=%s;"
        )
        return await self.cur.execute(query, (user_id, timestamp, timestamp))

    async def get_admin_last_seen(self, user_id: int):
        return await self.select_one(
            "SELECT last_seen FROM admin_status WHERE user_id=%s;",
            user_id
        )
        return await self.select_one(
            "SELECT time_give_food FROM Service;"
        )


    ### Referrals ###

    async def add_referral(self, referrer_id: int, referred_id: int):
        query = "INSERT IGNORE INTO Referrals (referrer_id, referred_id) VALUES (%s, %s);"
        await self.cur.execute(query, (referrer_id, referred_id))
        return self.cur.rowcount > 0

    async def get_referral_count(self, referrer_id: int):
        query = "SELECT COUNT(*) as cnt FROM Referrals WHERE referrer_id = %s;"
        await self.cur.execute(query, (referrer_id,))
        res = await self.cur.fetchone()
        return res["cnt"] if res else 0

    async def get_referral_list(self, referrer_id: int):
        query = "SELECT referred_id FROM Referrals WHERE referrer_id = %s;"
        await self.cur.execute(query, (referrer_id,))
        result = await self.cur.fetchall()
        return [row["referred_id"] for row in result] if result else []

    async def check_user_exists_in_db(self, user_id: int):
        query = "SELECT id FROM Users WHERE id = %s;"
        await self.cur.execute(query, (user_id,))
        return await self.cur.fetchone() is not None

    async def add_cases(self, id: int, case1: int = 1, case2: int = 0):
        query = 'UPDATE Lab SET case1 = case1 + %s, case2 = case2 + %s WHERE lab_id = %s;'
        await self.cur.execute(query, (case1, case2, id))
        await self.conn.commit()

    async def add_lab_epicoins(self, lab_id: int, amount: int):
        query = "UPDATE Lab SET epicoins = epicoins + %s WHERE lab_id = %s;"
        await self.cur.execute(query, (amount, lab_id))
        await self.conn.commit()

from asyncmy import Pool
from asyncmy.cursors import Cursor, DictCursor
from dataclasses import dataclass

import asyncio

@dataclass
class RequestsRepoChatManage:
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
    
    ### Add main elements ###
    
    
    ### Chat ###
    
    # bad idea with us database structure
    # async def chat_migrate_to_supergroup(self, chat_id: int, new_chat_id: int):
    #     query = """
    #         DELETE FROM Notes WHERE chat_id=%(chat_id)s;
    #         DELETE FROM Rules WHERE chat_id=%(chat_id)s;
    #         DELETE FROM Marriages WHERE chat_id=%(chat_id)s;
    #         DELETE FROM MarrigesBackups WHERE chat_id=%(chat_id)s;
    #         DELETE FROM Ship WHERE chat_id=%(chat_id)s;
    #         DELETE FROM Admins WHERE chat_id=%(chat_id)s;
    #         DELETE FROM ChatMemNotifications WHERE chat_id=%(chat_id)s;
    #         DELETE FROM Chat WHERE chat_id=%(chat_id)s;
    #     """
    #     params = {'new_chat_id': new_chat_id, 'chat_id': chat_id}
    #     await self.cur.execute(query, params)
    
    ### Notes ###
    
    # Get
    
    async def get_notes(self, chat_id: int):
        query = 'SELECT * FROM Notes WHERE chat_id=%s;'
        return await self.select_all(query, chat_id, False)
    
    async def get_note(self, chat_id: int, note_id: [int, str]):
        query = 'SELECT * FROM Notes WHERE chat_id=%s AND {}=%s;'
        request = await self.select_all(query.format('title'), (chat_id, note_id))
        if not request:
            request = await self.select_all(query.format('note_id'), (chat_id, note_id))
        return request
            
    async def get_notes_count(self, chat_id: int):
        count = await self.select_one('SELECT COUNT(*) FROM Notes WHERE chat_id=%s;', chat_id)
        return (count if count else 0)
    
    # Add
    
    async def add_note(self, chat_id: int, note_id: str, title: str, note_text: str):
        query = (
            'INSERT INTO Notes (chat_id, note_id, title, text) VALUES (%s, %s, %s, %s);'
        )
        params = (chat_id, note_id, title, note_text)
        await self.cur.execute(query, params)
    
    # Delete
    
    async def del_note(self, chat_id: int, note_id: int):
        query = 'DELETE FROM Notes WHERE chat_id=%s AND note_id=%s'
        params = (chat_id, note_id)
        await self.cur.execute(query, params)
    

    ### Marriages ###

    # Get

    async def get_users_marry_yet(self, chat_id: int, husband_id: int, wife_id: int):
        query = 'SELECT * FROM Marriages WHERE chat_id=%s AND (husband_id = %s AND wife_id = %s);'
        params = (chat_id, husband_id, wife_id)
        return await self.select_all(query, params)
    
    async def get_marry(self, chat_id: int, id: int):
        
        query = 'SELECT * FROM Marriages WHERE chat_id = %s AND (husband_id = %s OR wife_id = %s)'
        paramas = (chat_id, id, id)
        return await self.select_all(query, paramas)

    async def get_marry_backup(self, chat_id: int, ask_id: int, get_id):
        
        query = 'SELECT * FROM MarrigesBackups WHERE chat_id = %s AND (husband_id = %s AND wife_id = %s) OR (wife_id = %s AND husband_id = %s)'
        paramas = (chat_id, ask_id, get_id, ask_id, get_id)
        return await self.select_all(query, paramas)
    async def get_marriages_count(self, chat_id: int):
        count = await self.select_one('SELECT COUNT(*) FROM Marriages WHERE chat_id=%s;', chat_id)
        return (count if count else 0)

    async def get_all_marriages(self, chat_id: int):
        query = """
            SELECT u1.full_name AS full_name1, u2.full_name AS full_name2, m.husband_id, m.wife_id, sms_in_marriage, time_created FROM Marriages m
             INNER JOIN Users u1 ON u1.id = m.husband_id
             INNER JOIN Users u2 ON u2.id = m.wife_id 
            WHERE chat_id=%s ORDER BY time_created ASC;
        """
        params = chat_id
        return await self.select_all(query, params, use_index_zero=False)

    async def get_marry_description(self, chat_id: int, husband_id: int, wife_id: int):
        query = 'SELECT description FROM Marriages WHERE chat_id=%s AND (husband_id=%s AND wife_id=%s);'
        params = (chat_id, husband_id, wife_id)
        return await self.select_all(query, params)

    async def get_all_marriages_desc_by_sms(self, chat_id: int):
        query = """
            SELECT u1.full_name AS full_name1, u2.full_name AS full_name2, m.husband_id, m.wife_id, sms_in_marriage, time_created FROM Marriages m
             INNER JOIN Users u1 ON u1.id = m.husband_id
             INNER JOIN Users u2 ON u2.id = m.wife_id 
            WHERE chat_id=%s ORDER BY sms_in_marriage DESC;
        """
        params = chat_id
        return await self.select_all(query, params, use_index_zero=False)

    async def get_top_marriage_exp(self, chat_id: int):
        query = ('SELECT MAX(m.husband_id) AS max_husband_id, MAX(m.wife_id) AS max_wife_id,'
                 ' ANY_VALUE(u1.full_name) AS full_name1, ANY_VALUE(u2.full_name) AS full_name2, ANY_VALUE(b1.bio_experience) AS bio_experience1, ANY_VALUE(b2.bio_experience) AS bio_experience2 ' 
             'FROM Marriages m '
             'JOIN Lab b1 ON m.husband_id = b1.lab_id '
             'JOIN Lab b2 ON m.wife_id = b2.lab_id '
             ' JOIN Users u1 ON u1.id = m.husband_id '
             ' JOIN Users u2 ON u2.id = m.wife_id '
             'WHERE m.chat_id=%s '
             'GROUP BY b1.bio_experience + b2.bio_experience '
             'ORDER BY b1.bio_experience + b2.bio_experience DESC;')
        params = chat_id
        return await self.select_all(query, params, use_index_zero=False)

    # Addions/remove

    async def add_sms_marriages(self, chat_id: int, husband_id: int):
        query = 'UPDATE Marriages SET sms_in_marriage=sms_in_marriage+1 WHERE chat_id=%s AND husband_id=%s;'
        params = (chat_id, husband_id)
        await self.cur.execute(query, params)

    async def restore_marriage(self, chat_id: int, ask_id: int, get_id: int, time_created: int, marry_id: int, sms_in_marriage: int, sticker: str):
        query = (
            'INSERT INTO Marriages (chat_id, marry_id, husband_id, wife_id, time_created, sms_in_marriage, marry_sticker) VALUES (%s, %s, %s, %s, %s, %s, %s);'
        )
        params = (chat_id, marry_id, get_id, ask_id, time_created, sms_in_marriage)
        await self.cur.execute(query, params)

    async def add_marry(self, chat_id: int, ask_id: int, get_id: int, time_created: int, marry_id: int, sticker: str):
        query = (
            'INSERT INTO Marriages (chat_id, marry_id, husband_id, wife_id, time_created, marry_sticker) VALUES (%s, %s, %s, %s, %s, %s);'
        )
        params = (chat_id, marry_id, get_id, ask_id, time_created, sticker)
        await self.cur.execute(query, params)

    async def add_marriage_description(self, chat_id: int, husband_id: int, wife_id: int, description_text: str):
        query = 'UPDATE Marriages SET description = %s WHERE chat_id = %s AND husband_id = %s AND wife_id = %s;'
        params = (description_text, chat_id, husband_id, wife_id)
        await self.cur.execute(query, params)

    
    async def del_marry(self, chat_id: int, husband_id, wife_id: int, marry_id: int, time_created: int, now: int, sms: int):
        query = 'DELETE FROM Marriages WHERE chat_id = %s AND ((husband_id = %s AND wife_id = %s) OR (husband_id = %s AND wife_id = %s));'
        params = (chat_id, husband_id, wife_id, wife_id, husband_id)
        await self.cur.execute(query, params)

        query = 'UPDATE Marriages SET marry_id = marry_id = %s WHERE chat_id = %s AND marry_id > -1'
        params = (marry_id,chat_id)
        await self.cur.execute(query, params)

        query = ("""
            INSERT IGNORE INTO MarrigesBackups 
            (chat_id, husband_id, wife_id, delete_add, time_created, sms_in_marriage) 
            VALUES (%s, %s, %s, %s, %s, %s);
        """)
        params = (chat_id, husband_id, wife_id, now, time_created, sms)
        await self.cur.execute(query, params)
    
    async def del_marry_backup(self, chat_id: int, id: int):
        query = 'DELETE FROM MarrigesBackups WHERE chat_id = %s AND (wife_id = %s OR husband_id = %s)'
        params = (chat_id, id, id)
        await self.cur.execute(query, params)

    # Rules

    async def add_rules_chat(self, chat_id: int, rules: str):
        query = 'INSERT INTO Rules (chat_id, text) VALUES (%s, %s) ON DUPLICATE KEY UPDATE text = %s'
        params = (chat_id, rules, rules)
        await self.cur.execute(query, params)

    async def get_rules_chat(self, chat_id: int):
        query = 'SELECT text FROM Rules WHERE chat_id = %s;'
        return await self.select_all(query, chat_id)

    async def del_rules_chat(self, chat_id: int):
        query = 'DELETE FROM Rules WHERE chat_id = %s;'
        await self.cur.execute(query, chat_id)

    
    # Admins

    async def add_admins(self, chat_id: int, admin_names: list[str], admin_ids: list[int]):
        query = '''
        INSERT INTO Admins (chat_id, admin_id, admin_name) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE admin_name = VALUES(admin_name)
        '''
        
        params = [
            (chat_id, admin_id, name) 
            for admin_id, name in zip(admin_ids, admin_names)
        ]
        
        await self.cur.executemany(query, params)



    async def get_admins(self, chat_id: int):
        query = 'SELECT admin_id FROM Admins WHERE chat_id = %s;'
        return await self.select_all(query, chat_id, use_index_zero=False)

    async def get_admin_info(self, chat_id: int, id: int):
        query = 'SELECT * FROM Admins WHERE chat_id = %s AND admin_id = %s;'
        return await self.select_all(query, (chat_id, id))

    async def get_admins_info_list(self, chat_id: int):
        query = 'SELECT * FROM Admins WHERE chat_id = %s;'
        return await self.select_all(query, chat_id, use_index_zero=False)

    # Notifications

    async def include_off_notifications(self, chat_id, status):
        if status == 0:
            query = 'UPDATE ChatMemNotifications SET new_chat_member = 0 WHERE chat_id = %s;'
            params = chat_id
            await self.cur.execute(query, params)

        elif status == 1:
            query = 'UPDATE ChatMemNotifications SET new_chat_member = 1 WHERE chat_id = %s;'
            params = chat_id
            await self.cur.execute(query, params)

        elif status == 2:
            query = 'INSERT IGNORE INTO ChatMemNotifications (chat_id, new_chat_member, leave_chat_member, up_to_admin) VALUES (%s, %s, %s, %s);'
            params = (chat_id, 0, 0, 0)
            await self.cur.execute(query, params)

        elif status == 3:
            query = 'UPDATE ChatMemNotifications SET leave_chat_member = 0 WHERE chat_id = %s;'
            params = chat_id
            await self.cur.execute(query, params)

        elif status == 4:
            query = 'UPDATE ChatMemNotifications SET leave_chat_member = 1 WHERE chat_id = %s;'
            params = chat_id
            await self.cur.execute(query, params)


    async def get_regime_notifications(self, chat_id):
        query = 'SELECT * FROM ChatMemNotifications WHERE chat_id = %s;'
        params = chat_id
        return await self.select_all(query, params)

    # Ship
    async def get_shipper(self, chat_id):
        
        query = ('SELECT * FROM Chat' 
            ' INNER JOIN Users ON Chat.user_id = Users.id' 
            ' WHERE chat_id=%s'
            ' ORDER BY RAND() LIMIT 2;')

        params = chat_id
        return await self.select_all(query, params, use_index_zero=False)

    async def get_shipper_check(self, chat_id):
        query = 'SELECT * FROM Ship WHERE chat_id = %s;'
        params = chat_id
        return await self.select_all(query, params)

    async def add_ship(self, chat_id, partner1_id, partner2_id, time):
    
        query = 'INSERT INTO Ship (chat_id, partner1_id, partner2_id, time_shiped) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE time_shiped = %s, partner1_id = %s, partner2_id = %s;'
        params = (chat_id, partner1_id, partner2_id, time, time, partner1_id, partner2_id)
        await self.cur.execute(query, params)
    
    # set nickname
    async def set_nickname(self, user_id: int, nickname: str):
        query = ("""
            INSERT INTO user_nickname (user_id, nickname) 
            VALUES (%s, %s) ON DUPLICATE KEY UPDATE nickname=%s;
        """)
        await self.cur.execute(query, (user_id, nickname, nickname))
    
    async def get_nickname(self, user_id: int):
        query = 'SELECT * FROM user_nickname WHERE user_id=%s;'
        return await self.select_all(query, user_id)
    
    # Chat bot update

    async def delete_chat_member(self, user_id: int, chat_id: int):
        query = (
            'DELETE FROM Admins WHERE admin_id=%s AND chat_id=%s;'
            'DELETE FROM Chat WHERE user_id=%s AND chat_id=%s;'
        )
        params = (user_id, chat_id, user_id, chat_id)
        await self.cur.execute(query, params)
    
    # Admin

    async def get_pm_chats_count(self):
        return await self.select_one('SELECT COUNT(*) FROM Chat WHERE is_private=1;')

    async def get_public_chats_count(self):
        query = 'SELECT COUNT(DISTINCT chat_id) AS distinct_chat_count  FROM Chat  WHERE is_private = 0;'
        return await self.select_one(query)
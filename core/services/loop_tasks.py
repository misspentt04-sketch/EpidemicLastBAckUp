from aiogram import Bot

from asyncmy.pool import Pool
from asyncmy.cursors import DictCursor
from redis.asyncio import Redis

from datetime import datetime, timedelta
from cachetools import TTLCache

from core import func
from core.data.tricks.tricks_biowar import tricks_biowar
from core.data.tricks.tricks_genai import tricks_genai
from core.utils.genai import gpt_thinks
from core.settings import moscow_tz

import asyncio


async def victim_expire_check(pool: Pool):
    sql = 'SELECT victims_owner_id, victim_id FROM Victims WHERE victim_expire < %s;'
    sql1 = 'DELETE FROM Victims WHERE victims_owner_id = %s AND victim_id=%s;'
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(4*60*60)
                timestmp = int(datetime.utcnow().timestamp())
                await cur.execute(sql, timestmp)
                check = await cur.fetchall()
                for string in check:
                    victims_owner_id, victim_id = string.values()
                    await cur.execute(sql1, (victims_owner_id, victim_id))

async def victim_expire_kd_check(pool: Pool):
    sql = 'SELECT victims_owner_id, victim_id FROM Victims WHERE victim_expire_kd != 0 AND victim_expire_kd < %s;'
    sql1 = 'UPDATE Victims SET victim_expire_kd = 0 WHERE victims_owner_id=%s AND victim_id=%s;'
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(30)
                timestmp = int(datetime.utcnow().timestamp())
                await cur.execute(sql, timestmp)
                check = await cur.fetchall()
                for string in check:
                    id, vic_id = string.values()
                    await cur.execute(sql1, (id, vic_id))

async def victim_fever_check(pool: Pool):
    sql = 'SELECT lab_id FROM Lab WHERE fever IS NOT NULL AND fever < %s;'
    sql1 = 'UPDATE Lab SET fever=NULL WHERE lab_id = %s'
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(30)
                timestmp = int(datetime.utcnow().timestamp())
                await cur.execute(sql, timestmp)
                check = await cur.fetchall()
                for string in check:
                    await cur.execute(sql1, string['lab_id'])

async def pathogens_refresh_check(pool: Pool):
    sql = (
        'SELECT lab_id, science, pathogens, ready_pathogens FROM Lab'
        ' WHERE science_time IS NOT NULL AND science_time < %s;'
    )
    sql1 = 'UPDATE Lab SET science_time=NULL WHERE lab_id = %s;'
    sql2 = 'UPDATE Lab SET science_time=%s, ready_pathogens=ready_pathogens+%s WHERE lab_id = %s;'
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(30)
                timestmp = int(datetime.utcnow().timestamp())
                await cur.execute(sql, timestmp)
                check = await cur.fetchall()
                for string in check:
                    id, science_lvl, pathogens, ready_pathogens = string.values()
                    if pathogens == ready_pathogens:
                        await cur.execute(sql1, string['lab_id'])
                    fever_expire = int((datetime.utcnow() + timedelta(minutes=(61-science_lvl))).timestamp())
                    science_time = None if ready_pathogens == pathogens else fever_expire
                    add_pathogens = 0 if ready_pathogens == pathogens else 1
                    await cur.execute(sql2, (science_time, add_pathogens, id))

async def corporation_stats_refresh(pool: Pool):
    query = (
        'UPDATE Corporation c '
        'JOIN ( '
        '    SELECT corporation_code, SUM(bio_experience) AS exp, SUM(infected) AS inf '
        '    FROM CorporationMembers '
        '    GROUP BY corporation_code '
        ') cm ON c.invitation_code = cm.corporation_code '
        'SET c.bio_experience = cm.exp, c.infected = cm.inf;'
    )
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(60)
                await cur.execute(query)

# async def marriges_backups_del(pool: Pool, bot):
#     async with pool.acquire() as conn:
#         async with conn.cursor(DictCursor) as cur:
#             while True:
#                 await cur.execute('SELECT * FROM MarrigesBackups;')
#                 check = await cur.fetchall()
#                 for string in check:
#                     husband_id, wife_id, time, chat_id = string['husband_id'], string['wife_id'], string['delete_add'], string['chat_id']
#                     if int(time) != 0 and datetime.utcnow() > datetime.fromtimestamp(time):
                        
#                         await cur.execute('SELECT full_name FROM Users WHERE id = %s', husband_id)
#                         husband = await cur.fetchone()
#                         await cur.execute('SELECT full_name FROM Users WHERE id = %s', wife_id)
#                         wife = await cur.fetchone()

#                         text = await func.devorce_marry(husband_id, wife_id, husband['full_name'], wife['full_name'])
#                         await bot.send_message(chat_id=chat_id, text=text)
#                         await cur.execute('DELETE FROM MarriagesBackups WHERE husband_id = %s AND wife_id = %s', (husband_id, wife_id))
#                     await asyncio.sleep(30)


async def gave_victims_food(pool: Pool):
    # sql = 'SELECT time_give_food FROM Service;'
    # sql1 = 'INSERT IGNORE INTO Service (time_give_food) VALUES (%s);'
    sql2 = 'UPDATE Service SET time_give_food=%s;'
    sql3 = (
        'UPDATE Lab l JOIN ('
        ' SELECT victims_owner_id, SUM(victim_bio_resource_earn) AS bio_resource FROM Victims'
        ' GROUP BY victims_owner_id)'
        'v ON l.lab_id = v.victims_owner_id '
        'SET l.bio_resource = l.bio_resource+v.bio_resource;'
    )
    
    # delay = tricks_biowar['max']['time']['gave_victims_food']
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            # # initialization
            # await cur.execute(sql)
            # time_food = await cur.fetchone()
            # if not time_food:
            #     await cur.execute(sql1, int((datetime.utcnow() + timedelta(seconds=delay)).timestamp()))
            # # Loop
            # while True:
            #     await asyncio.sleep(1*60)
            #     await cur.execute(sql)
            #     time_food = await cur.fetchone()
            #     if datetime.fromtimestamp(time_food['time_give_food']) < datetime.utcnow():
            #         await cur.execute(sql2, int((datetime.utcnow() + timedelta(seconds=delay)).timestamp()))
            #         await cur.execute(sql3)
            now = datetime.now(moscow_tz)
            if now.hour < 12:
                next_dt = now.replace(hour=12, minute=0, second=0, microsecond=0)
            else:
                next_dt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_time_food = next_dt.timestamp()
            await cur.execute(sql3)
            await cur.execute(sql2, next_time_food)
    

# изменить логику чтобы измежать фор луп или перенести в mysql
async def refresh_pets_vuln_indicator(redis: Redis):
    while True:
        await asyncio.sleep(5)
        cursor = 0
        all_keys = []

        while True:
            cursor, keys = await redis.scan(cursor=cursor, match='[0-9]*', count=1000)
            all_keys.extend(keys)
            if cursor == 0:
                break
        
        async with redis.pipeline() as pipe:
            for key in all_keys:
                pipe.hget(key, 'pet_vuln_indicator')
            
            values = await pipe.execute()
            
            for key, val in zip(all_keys, values):
                val = float(val)
                if val+1 <= 100:
                    pipe.hset(key, 'pet_vuln_indicator', val+1)
                if val+1 >= 100:
                    pipe.hset(key, 'pet_vuln_indicator', 100)
            await pipe.execute()


async def game_mute_check(pool: Pool, redis: Redis, bot: Bot):
    
    sql = 'SELECT user_id FROM BioMute WHERE time_expire < %s;'
    sql1 = 'SELECT user_id FROM GameMute WHERE time_expire < %s;'
    sql2 = 'DELETE FROM BioMute WHERE user_id=%s;'
    sql3 = 'DELETE FROM GameMute WHERE user_id=%s;'

    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(4*60*60)
                timestmp = int(datetime.utcnow().timestamp())
                await cur.execute(sql, timestmp)
                biomute = await cur.fetchall()
                await cur.execute(sql1, timestmp)
                gamemute = await cur.fetchall()
                for string in biomute:
                    user_id = string['user_id']
                    await cur.execute(sql2, user_id)
                    text = (
                        f'Вам был снят мут на наименования\n\n'
                        'Пожалуйста прочтите <a href="https://telegra.ph/CHego-luchshe-ne-stoit-delat-05-31">Правила игры</a> чтобы подать апеляцию пишите админам <a href="https://t.me/epidemic_biowar">здесь</a>'
                    )
                    try:
                        await bot.send_message(user_id, text, disable_web_page_preview=True)
                    except:
                        pass
                for string in gamemute:
                    user_id, time_expire = string.values()
                    await cur.execute(sql3, user_id)
                    await redis.delete(f'epidemic_gamemute:{user_id}')
                    text = (
                        f'Вам был снят игровой мут\n\n'
                        'Пожалуйста прочтите <a href="https://telegra.ph/CHego-luchshe-ne-stoit-delat-05-31">Правила игры</a> чтобы подать апеляцию пишите админам <a href="https://t.me/epidemic_biowar">здесь</a>'
                    )
                    try:
                        await bot.send_message(user_id, text, disable_web_page_preview=True)
                    except:
                        pass

async def pet_the_pet_time_check(pool: Pool, redis: Redis, bot: Bot):
    sql = 'SELECT DISTINCT(owner_pet_id), current_pet FROM Pets WHERE pet_the_pet_time != 0 AND pet_the_pet_time < %s;'
    sql1 = 'SELECT last_message_id, chat_id FROM user_chat_messages WHERE user_id=%s;'
    sql2 = 'UPDATE Pets SET pet_the_pet_time=0 WHERE owner_pet_id=%s;'
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(120)
                timestmp = int(datetime.utcnow().timestamp())
                await cur.execute(sql, timestmp)
                check = await cur.fetchall()
                for string in check:
                    user_id, current_pet = string.values()
                    await cur.execute(sql1, user_id)
                    fetch = await cur.fetchall()
                    await cur.execute(sql2, user_id)
                    if fetch:
                        last_msg, chat_id = fetch[0].values()
                        try:
                            text = gpt_thinks(
                                tricks_genai['prompts']['pets'][current_pet]['pet_the_pet_notify'].format(current_pet.title()))
                            text_formatted = text.replace(current_pet.title(), f'<b>{current_pet.title()}</b>')
                            bot_answer_msg = await bot.send_message(text=text_formatted, chat_id=chat_id, reply_to_message_id=last_msg)
                        except Exception as e:
                            print(e)
                            pass
                        else:
                            await redis.set(
                                f'epidemic_pet_msg:{chat_id}:{bot_answer_msg.message_id}',
                                f'{user_id}:{current_pet}:pet_notify:{text}'
                            )

async def pet_happy_check(pool: Pool):
    sql = 'SELECT DISTINCT(owner_pet_id), happy FROM Pets;'
    sql1 = 'UPDATE Pets SET happy=%s WHERE owner_pet_id=%s;'
    
    async with pool.acquire() as conn:
        async with conn.cursor(DictCursor) as cur:
            while True:
                await asyncio.sleep(1*60*60) # fixed value, don't touch
                await cur.execute(sql)
                check = await cur.fetchall()
                for string in check:
                    user_id, happy = string.values()
                    happy_result = func.adjust_value(happy, tricks_biowar['max']['pet_happy_for_hour_percent'], '-')
                    await cur.execute(sql1, (happy_result, user_id))


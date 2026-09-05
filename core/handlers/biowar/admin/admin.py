from aiogram.types import Message
from aiogram import Bot
from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from aiogram.filters import Command
from aiogram import Router
admin_router = Router()
from aiogram import types, Bot
from aiogram.filters import CommandObject

from redis import Redis
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.utils.db_api.repo_chat_manage import RequestsRepoChatManage
from core import func
from core.settings import CHAT_LOGS

from humanize import intcomma
from datetime import datetime, timedelta

import asyncio
import sys

async def search_pathogen(
        message: types.Message,
        repo_biowar: RequestsRepoBiowar,
        command: CommandObject
):
    args = command.args

    q = f"SELECT lab_id, lab_name, pathogen_name FROM Lab WHERE pathogen_name LIKE '%{args}%';"
    result = await repo_biowar.select_all(q, use_index_zero=False)

    if not result:
        text = '❌ Ни у кого нет такого патогена'
    else:
        text = f'📝 Список людей содержащие в имени патогена "{args}":'
        for index, i in enumerate(result, start=1):
            text += f"\n{index}. {func.entity_create_full_name(i['lab_id'], i['lab_name'])}: {i['pathogen_name']}"
    await message.reply(text)

async def all_game_bio_experience(msg: types.Message, repo_biowar: RequestsRepoBiowar, command: CommandObject):
    
    args = command.args
    
    result = await repo_biowar.select_one('SELECT SUM(bio_experience) FROM Lab;')
    
    await msg.answer(intcomma(int(result)))

async def pathogen_mute(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    
    mute_days = int(msg.text.split()[1])
    mute_time = int((datetime.utcnow() + timedelta(days=mute_days)).timestamp())
    user_link = func.reply_or_tag_geeter(msg)
    reason = ' '.join(msg.text.split()[3:] if func.link_getter(msg.text) else msg.text.split()[2:])
    
    user = await repo_biowar.get_user(user_link)
    corp = await repo_biowar.get_corporation(user['id'])
    mention = func.entity_create(user['id'], user['full_name'])
    lab_name = 'лаб ' + user['full_name']
    admin_user = await repo_biowar.get_user(msg.from_user.id)
    admin_mention = func.entity_create_consider_username(admin_user)
    
    await repo_biowar.bio_mute(user['id'], lab_name, corp, mute_time, msg.from_user.id, reason)
    
    text = (
        f'Игроку {mention} выдан мут на изменение игровых имен на {mute_days} дней\n'
        f'Причина: {reason}'
    )
    mute_text = (
        f'Вам выдан мут на изменение игровых наименований на {mute_days} дней\n\n'
        f'<b>Причина:</b><i> {reason}</i>\n'
        f'<b>Кем выдан:</b> Telegram\n\n'
        '<a href="https://telegra.ph/CHego-luchshe-ne-stoit-delat-05-31">Правила игры</a> чтобы подать апеляцию пишите админам <a href="https://t.me/epidemic_biowar">здесь</a>'
    )
    
    text_to_moder_chat = (
        f'Игроку {mention} выдан мут на изменение игровых имен на {mute_days} дней\n'
        f'<b>Причина:</b> <i>{reason}</i>\n'
        f'<b>Кем выдан:</b> <i>Telegram</i>\n'
    )

    await msg.answer(text)
    await asyncio.sleep(1)
    try:
        await bot.send_message(user['id'], mute_text, disable_web_page_preview=True)
    except:
        pass
    await asyncio.sleep(1)
    # try:
    #     await bot.send_message(CHAT_MODERS, text_to_moder_chat, disable_web_page_preview=True)
    # except:
    #     pass

async def pathogen_mute_cancel(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar, redis: Redis):
    
    user_link = func.reply_or_tag_geeter(msg)
    
    user = await repo_biowar.get_user(user_link)

    biomute = await repo_biowar.get_user_bio_mute(user['id'])
    mention = func.entity_create(user['id'], user['full_name'])
    admin_user = await repo_biowar.get_user(msg.from_user.id)
    admin_mention = func.entity_create_consider_username(admin_user)
    
    await repo_biowar.bio_mute_cancel(user['id'])

    text = f'Игроку {mention} был снят мут на наименования'
    mute_text = (
        f'Вам был снят мут на наименования\n\n'
        'Пожалуйста прочтите <a href="https://teletype.in/@epidemic_gamebot/guide_epidemic">Правила игры</a> чтобы подать апеляцию пишите админам <a href="https://t.me/https://t.me/biowars_chat">здесь</a>'
    )
    
    text_to_moder_chat = (
        f'Игроку {mention} был снят игровой мут\n'
        f'<b>Причина:</b> <i>{biomute["reason"] if biomute["reason"] else "нету"}</i>\n'
        f'<b>Кем снят:</b> <i>Telegram</i>'
    )

    await msg.answer(text)
    await asyncio.sleep(1)
    try:
        await bot.send_message(user['id'], mute_text, disable_web_page_preview=True)
    except:
        pass
    # try:
    #     await bot.send_message(CHAT_MODERS, text_to_moder_chat, disable_web_page_preview=True)
    # except:
    #     pass

async def game_mute(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar, redis: Redis):
    
    mute_days = int(msg.text.split()[1])
    mute_time = int((datetime.utcnow() + timedelta(days=mute_days)).timestamp())
    user_link = func.reply_or_tag_geeter(msg)
    reason = ' '.join(msg.text.split()[3:] if func.link_getter(msg.text) else msg.text.split()[2:])

    user = await repo_biowar.get_user(user_link)
    admin_user = await repo_biowar.get_user(msg.from_user.id)
    mention = func.entity_create(user['id'], user['full_name'])
    admin_mention = func.entity_create_consider_username(admin_user)

    await repo_biowar.game_mute(user['id'], mute_time, msg.from_user.id, reason)
    await redis.set(f'epidemic_gamemute:{user["id"]}', mute_time)

    text = (
        f'Игроку {mention} выдан игровой мут на {mute_days} дней\n'
        f'Причина: {reason}'
    )
    mute_text = (
        f'Вам выдан игровой мут на <b>{mute_days}</b> дней(игровые команды не будут на вас реагировать)\n'
        f'<b>Причина:</b><i> {reason}</i>\n'
        f'<b>Кем выдан:</b> Telegram\n\n'
        '<a href="https://telegra.ph/CHego-luchshe-ne-stoit-delat-05-31">Правила игры</a> чтобы подать апеляцию пишите админам <a href="https://t.me/epidemic_biowar">здесь</a>'
    )

    text_to_moder_chat = (
        f'Игроку {mention} выдан игровой мут на {mute_days} дней\n'
        f'<b>Причина:</b> <i>{reason}</i>\n'
        f'<b>Кем выдан:</b> <i>Telegram</i>\n'
    )
    
    await msg.answer(text)
    await asyncio.sleep(1)
    try:
        await bot.send_message(user['id'], mute_text, disable_web_page_preview=True)
    except:
        pass
    await asyncio.sleep(1)
    # try:
    #     await bot.send_message(CHAT_MODERS, text_to_moder_chat, disable_web_page_preview=True)
    # except:
    #     pass

async def game_mute_cancel(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar, redis: Redis):
    
    user_link = func.reply_or_tag_geeter(msg)

    user = await repo_biowar.get_user(user_link)

    gamemute = await repo_biowar.get_user_game_mute(user['id'])
    mention = func.entity_create(user['id'], user['full_name'])
    admin_user = await repo_biowar.get_user(msg.from_user.id)
    admin_mention = func.entity_create_consider_username(admin_user)

    await repo_biowar.game_mute_cancel(user['id'])
    await redis.delete(f'epidemic_gamemute:{user["id"]}')

    text = f'Игроку {mention} был снят игровой мут'
    mute_text = (
        f'Вам был снят игровой мут\n\n'
        'Пожалуйста прочтите <a href="https://telegra.ph/CHego-luchshe-ne-stoit-delat-05-31">Правила игры</a> чтобы подать апеляцию пишите админам <a href="https://t.me/epidemic_biowar">здесь</a>'
    )

    text_to_moder_chat = (
        f'Игроку {mention} был снят игровой мут\n'
        f'<b>Причина:</b> <i>{gamemute["reason"] if gamemute["reason"] else "Нету"}</i>\n'
        f'<b>Кем снят:</b> <i>Telegram</i>'
    )
    
    await msg.answer(text)
    await asyncio.sleep(1)
    try:
        await bot.send_message(user['id'], mute_text, disable_web_page_preview=True)
    except:
        pass
    # try:
    #     await bot.send_message(CHAT_MODERS, text_to_moder_chat, disable_web_page_preview=True)
    # except:
    #     pass


async def lab_transfer(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    
    parts = msg.text.split()

    admin_user = await repo_biowar.get_user(msg.from_user.id)
    admin_mention = func.entity_create(admin_user['id'], admin_user['full_name'])

    lab_from = await repo_biowar.get_info_user_lab(func.link_getter(parts[1]))
    lab_to = await repo_biowar.get_info_user_lab(func.link_getter(parts[2]))
    
    game_mute = await repo_biowar.get_user_game_mute(lab_from['lab_id'])
    
    if game_mute:
        return await msg.answer('Лаборатория не может быть перенесена дак как игрок имеет игровой мут')
    
    bag_from = await repo_biowar.get_bag(func.link_getter(parts[1]))
    bag_to = await repo_biowar.get_bag(func.link_getter(parts[2]))
    
    pet_from = await repo_biowar.get_my_pet(func.link_getter(parts[1]))

    await repo_biowar.lab_tranfer(lab_from, lab_to, bag_from, bag_to, pet_from)
    
    mention_from = func.entity_create(lab_from['lab_id'], lab_from['full_name'])
    mention_to = func.entity_create(lab_to['lab_id'], lab_to['full_name'])
    
    text = f'Лаба перенесена с {mention_from} на {mention_to} аккаунт эпидемика'
    text_to_moder_chat = (
        f'Лаба перенесена с {mention_from} на {mention_to} аккаунт эпидемика\n'
        f'<b>Кто перенес:</b> <i>{admin_mention}</i>'
    )    

    await msg.answer(text)
    await asyncio.sleep(1)
    # try:
    #     await bot.send_message(CHAT_MODERS, text_to_moder_chat)
    # except:
    #     pass
    
async def le(msg: types.Message):
    await msg.answer('Le')

async def stop_bot(msg: types.Message):
    await msg.answer('Эпидемик бот отключен.')
    sys.exit(0)

async def biomute_list(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    
    biomute_users = await repo_biowar.get_biomute_list()

    biomute_list = await func.get_biomute_list(repo_biowar, biomute_users)
    
    text = f'<b>Список игроков с биомутом</b>\n' + '\n'.join(biomute_list)
    
    await msg.answer(text, disable_web_page_preview=True)

async def gamemute_list(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    
    biomute_users = await repo_biowar.get_gamemute_list()

    biomute_list = await func.get_gamemute_list(repo_biowar, biomute_users)
    
    text = f'<b>Список игроков с эпиасом</b>\n' + '\n'.join(biomute_list)
    
    await msg.answer(text, disable_web_page_preview=True)

async def check_the_mute(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    
    user_link = func.reply_or_tag_geeter(msg)
    user = await repo_biowar.get_user(user_link)

    biomute = await repo_biowar.get_user_bio_mute(user['id'])
    gamemute = await repo_biowar.get_user_game_mute(user['id'])


    text = ''

    if biomute:
        biomute_admin = await repo_biowar.get_user(biomute['admin'])
        admin_mention = func.entity_create_consider_username(biomute_admin)
        text += (
            '<b>Биомут</b>\n'
            f'Кем выдан: {admin_mention}\n'
            f'Причина: <i>{biomute["reason"]}</i>\n\n'
        )
    if gamemute:
        gamemute_admin = await repo_biowar.get_user(gamemute['admin'])
        admin_mention = func.entity_create_consider_username(gamemute_admin)
        text += (
            '<b>Эпиас</b>\n'
            f'Кем выдан: {admin_mention}\n'
            f'Причина: <i>{gamemute["reason"]}</i>'
        )
    if not gamemute and not biomute:
        text = 'У игрока нету ограничений'

    await msg.answer(text, disable_web_page_preview=True)

async def bot_statistics(msg: types.Message, bot: Bot, repo_biowar: RequestsRepoBiowar, repo_cm: RequestsRepoChatManage):
    
    pm_chats_count = await repo_cm.get_pm_chats_count()
    public_chats_count = await repo_cm.get_public_chats_count()
    game_exp = await repo_biowar.select_one('SELECT SUM(bio_experience) FROM Lab;')

    text = (
        '<b>📊 Статистика бота</b>\n'
        f'Личек с ботом: <b>{pm_chats_count}</b>\n'
        f'Публичных чатов: <b>{public_chats_count}</b>\n'
        f'Опыт игры: <b>{intcomma(game_exp)}</b>'
    )
    
    await msg.answer(text)
    

    chat_id = msg.chat.id
    await msg.answer("🔍 Сканирую участников чата...")

    count = 0
    async for member in bot.get_chat_members(chat_id):
        user = member.user
        if not user.is_bot:
            try:
                await repo_biowar.add_data_user(
                    user.id,
                    user.full_name or "Без имени",
                    user.username
                )
                count += 1
            except Exception:
                pass

    await msg.answer(f"✅ Зарегистрировано {count} пользователей из этого чата!")


    total_chats = 0
    total_users = 0
    report = []

    try:
        # Получаем все чаты, где есть бот
        async for dialog in bot.get_dialogs():
            chat = dialog.chat
            chat_id = chat.id
            chat_title = chat.title or chat.full_name or str(chat_id)

            try:
                # Пропускаем личные сообщения
                if chat.type == "private":
                    continue

                total_chats += 1
                users_in_chat = 0

                # Сканируем участников чата
                async for member in bot.get_chat_members(chat_id):
                    user = member.user
                    if not user.is_bot:
                        try:
                            await repo_biowar.add_data_user(
                                user.id,
                                user.full_name or "Без имени",
                                user.username
                            )
                            users_in_chat += 1
                            total_users += 1
                        except Exception:
                            pass

                report.append(f"✅ {chat_title}: {users_in_chat} пользователей")
                await asyncio.sleep(0.5)  # небольшая задержка чтобы не спамить Telegram

            except Exception as e:
                report.append(f"❌ {chat_title}: ошибка - {str(e)[:50]}")

    except Exception as e:
        await msg.answer(f"❌ Ошибка сканирования: {e}")
        return

    # Отправляем отчёт
    report_text = (
        f"📊 <b>ИТОГИ СКАНИРОВАНИЯ</b>\n\n"
        f"📁 Проверено чатов: <b>{total_chats}</b>\n"
        f"👤 Всего записано пользователей: <b>{total_users}</b>\n\n"
        f"<b>Детали по чатам:</b>\n"
        f"{chr(10).join(report[-20:])}"  # показываем последние 20 чатов
    )

    if len(report) > 20:
        report_text += f"\n\n<i>...и ещё {len(report) - 20} чатов</i>"

    await msg.answer(report_text, parse_mode="HTML")

@admin_router.message(Command("scan_all_chats"))
async def scan_all_chats(msg: Message, bot: Bot, repo_biowar: RequestsRepoBiowar):
    if msg.from_user.id not in [7972320837]:
        return

    await msg.answer("🔍 Сканирую ВСЕ чаты, где есть бот... Это может занять время.")

    total_chats = 0
    total_users = 0
    report = []

    try:
        async for dialog in bot.get_dialogs():
            chat = dialog.chat
            chat_id = chat.id
            chat_title = chat.title or chat.full_name or str(chat_id)

            if chat.type == "private":
                continue

            total_chats += 1
            users_in_chat = 0

            async for member in bot.get_chat_members(chat_id):
                user = member.user
                if not user.is_bot:
                    try:
                        await repo_biowar.add_data_user(
                            user.id,
                            user.full_name or "Без имени",
                            user.username
                        )
                        users_in_chat += 1
                        total_users += 1
                    except Exception:
                        pass

            report.append(f"✅ {chat_title}: {users_in_chat} пользователей")
            await asyncio.sleep(0.5)

    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")
        return

    report_text = (
        f"📊 <b>ИТОГИ СКАНИРОВАНИЯ</b>\n\n"
        f"📁 Проверено чатов: <b>{total_chats}</b>\n"
        f"👤 Всего записано пользователей: <b>{total_users}</b>\n\n"
        f"<b>Детали по чатам:</b>\n"
        f"{chr(10).join(report[-20:])}"
    )

    if len(report) > 20:
        report_text += f"\n\n<i>...и ещё {len(report) - 20} чатов</i>"

    await msg.answer(report_text, parse_mode="HTML")

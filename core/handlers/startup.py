import logging
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import CommandObject
from aiogram import Bot

from redis import Redis
from asyncmy.cursors import Cursor

from core.utils.db_api.repo_biowar import RequestsRepoBiowar
from core.data.story.story import tricks_story
from core.data.tricks.tricks_chat_manage import tricks_cm
from core.keyboards.inline.tutorial_begin import start_action, help_kb

logger = logging.getLogger(__name__)

LOG_CHAT_ID = -1003688648228
REFERRAL_BONUS = 150

async def start(msg: Message, command: CommandObject, db: Cursor, bot: Bot, redis: Redis, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    full_name = msg.from_user.full_name
    username = msg.from_user.username
    args = command.args

    print(f"\n[REF_DEBUG] --- Новый запуск /start от user_id={user_id}, args={args} ---")

    # 1. Проверяем существование пользователя ДО add_data_user
    user_exists = False
    try:
        user_exists = await repo_biowar.check_user_exists_in_db(user_id)
        print(f"[REF_DEBUG] check_user_exists_in_db={user_exists}")
    except Exception as e:
        print(f"[REF_DEBUG] Ошибка check_user_exists_in_db: {e}")

    # 2. Добавляем / обновляем пользователя
    try:
        await repo_biowar.add_data_user(user_id, full_name, username)
        print(f"[REF_DEBUG] add_data_user выполнено успешно")
    except Exception as e:
        print(f"[REF_DEBUG] Ошибка add_data_user: {e}")

    # 3. Обработка реферала
    if args:
        ref_arg = args.strip()
        print(f"[REF_DEBUG] Аргумент передан: {ref_arg}")
        if ref_arg.startswith("ref"):
            try:
                referrer_id = int(ref_arg.replace("ref", ""))
                print(f"[REF_DEBUG] Определен referrer_id={referrer_id}")
                
                if referrer_id != user_id:
                    # Запись в таблицу Referrals
                    try:
                        added = await repo_biowar.add_referral(referrer_id, user_id)
                        print(f"[REF_DEBUG] Результат add_referral={added}")
                    except Exception as ref_e:
                        print(f"[REF_DEBUG] ОШИБКА add_referral в БД: {ref_e}")
                        added = False

                    if added:
                        # Проверка лимита в 50 рефералов
                        ref_cnt = await repo_biowar.get_referral_count(referrer_id)
                        if ref_cnt <= 50:
                            # 1. Начисление +150 Epicoins за каждого реферала до 50
                            try:
                                await repo_biowar.add_lab_epicoins(referrer_id, 150)
                                print(f"[REF_DEBUG] +150 Epicoins id={referrer_id} ({ref_cnt}/50)")
                            except Exception as bonus_e:
                                print(f"[REF_DEBUG] ОШИБКА epicoins: {bonus_e}")

                            # 2. Начисление кейсов по вехам
                            case1_to_add = 0
                            case2_to_add = 0

                            if ref_cnt in [5, 10, 35, 40]:
                                case1_to_add = 1
                            elif ref_cnt == 15:
                                case1_to_add = 2
                            elif ref_cnt in [30, 50]:
                                case2_to_add = 1

                            if case1_to_add > 0 or case2_to_add > 0:
                                try:
                                    await repo_biowar.add_cases(referrer_id, case1=case1_to_add, case2=case2_to_add)
                                    print(f"[REF_DEBUG] Выданы кейсы id={referrer_id}: case1={case1_to_add}, case2={case2_to_add}")
                                except Exception as case_e:
                                    print(f"[REF_DEBUG] ОШИБКА кейсов: {case_e}")
                        else:
                            print(f"[REF_DEBUG] Лимит 50 рефералов превышен ({ref_cnt}). Награды id={referrer_id} НЕ начислены.")

                        # Отправка в чат логов
                        try:
                            await bot.send_message(
                                LOG_CHAT_ID,
                                f"👤 <b>Новый реферал!</b>\n"
                                f"🆔 Пригласивший: <code>{referrer_id}</code>\n"
                                f"🆕 Новый игрок: {full_name} (<code>{user_id}</code>)\n"
                                f"🎁 Бонус: +{REFERRAL_BONUS} Эпи-коинов."
                            )
                            print(f"[REF_DEBUG] Лог успешно отправлен в {LOG_CHAT_ID}")
                        except Exception as log_e:
                            print(f"[REF_DEBUG] ОШИБКА отправки сообщения в лог-чат: {log_e}")

                        # Отправка в ЛС пригласившему
                        try:
                            await bot.send_message(
                                referrer_id,
                                f"🎉 По вашей ссылке зарегистрировался новый игрок {full_name}!\n"
                                f"🎁 Вам начислено <b>+{REFERRAL_BONUS}</b> Эпи-коинов."
                            )
                            print(f"[REF_DEBUG] Уведомление отправлено пригласившему id={referrer_id}")
                        except Exception as pm_e:
                            print(f"[REF_DEBUG] ОШИБКА отправки в ЛС пригласившему: {pm_e}")

            except ValueError as ve:
                print(f"[REF_DEBUG] Неверный формат ref_arg: {ve}")

    # 4. Основная логика туториала
    try:
        await repo_biowar.add_data_tutorial(user_id)
        picture = await redis.get('epidemic_tutorial_begin_img')
        tutorial = await repo_biowar.get_tutorial(user_id)

        if tutorial and tutorial.get('is_tutorial_complete') == 0:
            if not picture:
                with open('media/tutorial_begin.jpg', 'rb') as img:
                    result = await msg.answer_photo(
                        BufferedInputFile(img.read(), filename='tutorial_begin.jpg'),
                        caption=tricks_story['start_action'],
                        reply_markup=start_action(),
                        disable_web_page_preview=True
                    )
                    await redis.set('epidemic_tutorial_begin_img', result.photo[-1].file_id)
            else:
                await msg.answer_photo(
                    picture,
                    caption=tricks_story['start_action'],
                    reply_markup=start_action(),
                    disable_web_page_preview=True
                )
        else:
            admin_list = tricks_cm['start']['menu_admin_list']
            online = [val for key, val in admin_list.items() if await redis.get(f'epidemic_help_admin_status:{key}')]
            offline = [val for key, val in admin_list.items() if not await redis.get(f'epidemic_help_admin_status:{key}')]

            text = tricks_cm['start']['menu'].format('\n'.join(online), '\n'.join(offline))
            await msg.answer(text, reply_markup=help_kb(), disable_web_page_preview=True)

    except Exception as tut_e:
        print(f"[REF_DEBUG] Ошибка в блоке туториала: {tut_e}")

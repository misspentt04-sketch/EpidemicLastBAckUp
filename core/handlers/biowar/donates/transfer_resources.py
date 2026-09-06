import re
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()

MAX_TRANSFER_PERCENT = 100  # 100% от дохода получателя за тик
ADMIN_ID = 7972320837
LOG_CHAT = -1003688648228

# ===== ФУНКЦИЯ ОТПРАВКИ УВЕДОМЛЕНИЙ =====
async def send_transfer_notifications(bot: Bot, sender_id: int, target_id: int, amount: int, chat_id: int, message_id: int, repo_biowar: RequestsRepoBiowar):
    """Отправляет уведомления админу и получателю"""
    try:
        # Получаем имена
        sender_name = None
        target_name = None

        # Получаем отправителя
        await repo_biowar.cur.execute("SELECT full_name FROM Users WHERE id = %s;", (sender_id,))
        sender_data = await repo_biowar.cur.fetchone()
        if sender_data:
            sender_name = sender_data[0] if isinstance(sender_data, (tuple, list)) else sender_data.get('full_name')

        # Получаем получателя
        await repo_biowar.cur.execute("SELECT full_name FROM Users WHERE id = %s;", (target_id,))
        target_data = await repo_biowar.cur.fetchone()
        if target_data:
            target_name = target_data[0] if isinstance(target_data, (tuple, list)) else target_data.get('full_name')

        if not sender_name:
            sender_name = f"ID {sender_id}"
        if not target_name:
            target_name = f"ID {target_id}"

        # Ссылка на сообщение в группе
        message_link = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}" if str(chat_id).startswith("-100") else f"https://t.me/c/{chat_id}/{message_id}"

        # 1. Уведомление АДМИНУ (в ЛС)
        try:
            admin_text = (
                f"📩 <b>Передача ресурсов</b>\n\n"
                f"📤 Отправитель: <b>{sender_name}</b> (<code>{sender_id}</code>)\n"
                f"📥 Получатель: <b>{target_name}</b> (<code>{target_id}</code>)\n"
                f"🧬 Количество: <b>{amount:,}</b> ресурсов\n"
                f"🔗 <a href='{message_link}'>Ссылка на сообщение</a>"
            )
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            print(f"[ADMIN NOTIFY ERROR] {e}")

        # 2. Уведомление в ЛОГ-ЧАТ
        try:
            log_text = (
                f"📩 <b>Передача ресурсов</b>\n\n"
                f"📤 От: <code>{sender_id}</code> ({sender_name})\n"
                f"📥 Кому: <code>{target_id}</code> ({target_name})\n"
                f"🧬 Сумма: <b>{amount:,}</b>"
            )
            await bot.send_message(LOG_CHAT, log_text, parse_mode="HTML")
        except Exception as e:
            print(f"[LOG CHAT ERROR] {e}")

        # 3. Уведомление ПОЛУЧАТЕЛЮ (в ЛС)
        try:
            receiver_text = (
                f"🎁 <b>Вам передали ресурсы!</b>\n\n"
                f"🧬 Получено: <b>{amount:,}</b> ресурсов\n"
                f"📤 От: <b>{sender_name}</b> (<code>{sender_id}</code>)"
            )
            await bot.send_message(target_id, receiver_text, parse_mode="HTML")
        except Exception as e:
            print(f"[RECEIVER NOTIFY ERROR] {e}")

        # 4. Уведомление ОТПРАВИТЕЛЮ (в ЛС)
        try:
            sender_text = (
                f"✅ <b>Вы передали ресурсы!</b>\n\n"
                f"🧬 Передано: <b>{amount:,}</b> ресурсов\n"
                f"📥 Кому: <b>{target_name}</b> (<code>{target_id}</code>)"
            )
            await bot.send_message(sender_id, sender_text, parse_mode="HTML")
        except Exception as e:
            print(f"[SENDER NOTIFY ERROR] {e}")

    except Exception as e:
        print(f"[TRANSFER NOTIFY ERROR] {e}")

# ===== ОСНОВНАЯ КОМАНДА ПЕРЕДАЧИ =====
@router.message(F.text.regexp(r'^(\.|/|!)?(отдать|передать)\s+(ресурс(ы|ов)?|рес(ы|ов)?|ресы?)\s+', flags=re.IGNORECASE))
async def cmd_transfer_resources(msg: Message, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    args = msg.text.split()
    
    target_id = None
    amount = 0
    
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
    
    if not target_id:
        for arg in args:
            if arg.startswith('@'):
                clean_arg = arg[1:]
                if clean_arg.isdigit():
                    target_id = int(clean_arg)
                else:
                    await repo_biowar.cur.execute(
                        "SELECT lab_id FROM Lab WHERE lab_id IN (SELECT id FROM Users WHERE username = %s);",
                        (clean_arg,)
                    )
                    lab = await repo_biowar.cur.fetchone()
                    if lab:
                        target_id = lab[0] if isinstance(lab, (tuple, list)) else lab.get('lab_id')
                break
            elif arg.isdigit() and len(arg) > 5:
                target_id = int(arg)
                break
    
    digits = [int(arg) for arg in args if arg.isdigit()]
    if digits:
        amount = digits[-1]
    
    if not target_id or amount <= 0:
        await msg.reply(
            "❌ <b>Неверный формат!</b>\n\n"
            "✅ <b>Правильно:</b>\n"
            "<code>.отдать ресурсы @username 1000</code>\n"
            "<code>/передать ресы @id 5000</code>\n"
            "<code>!отдать ресурсы 123456789 10000</code>\n"
            "<code>.отдать ресурсы</code> (реплаем) <code>5000</code>\n\n"
            "📝 <b>Кому:</b> @username, @123456789, 123456789, или реплай\n"
            "🔢 <b>Сколько:</b> число больше 0\n\n"
            "📋 <b>Доступные команды:</b>\n"
            "• <code>.баланс</code> или <code>баланс</code> — проверить ресурсы\n"
            "• <code>!баланс</code> или <code>/баланс</code> — проверить ресурсы\n"
            "• <code>.рес</code> или <code>рес</code> — проверить ресурсы\n"
            "• <code>.лимит</code> или <code>лимит</code> — проверить лимит\n"
            "• <code>.помощь</code> или <code>помощь</code> — все команды",
            parse_mode="HTML"
        )
        return
    
    if target_id == user_id:
        await msg.reply("❌ Нельзя передать самому себе!")
        return
    
    # Проверяем ресурсы отправителя
    await repo_biowar.cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await repo_biowar.cur.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return
    
    current_resources = lab[0] if isinstance(lab, (tuple, list)) else lab.get('bio_resource', 0) or 0
    
    if current_resources < amount:
        await msg.reply(f"❌ Недостаточно! У вас: <b>{current_resources:,}</b>", parse_mode="HTML")
        return
    
    # Проверяем получателя и его доход за тик
    await repo_biowar.cur.execute("""
        SELECT l.lab_id, l.bio_resource, 
               COALESCE(SUM(v.victim_bio_resource_earn) * (1 + COALESCE(l.rebirth_level, 0) * 0.10), 0) AS tick_income
        FROM Lab l
        LEFT JOIN Victims v ON v.victims_owner_id = l.lab_id
        WHERE l.lab_id = %s
        GROUP BY l.lab_id
    """, (target_id,))
    target_data = await repo_biowar.cur.fetchone()
    
    if not target_data:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден!")
        return
    
    if isinstance(target_data, dict):
        tick_income = float(target_data.get('tick_income', 0) or 0)
    else:
        tick_income = float(target_data[2] if len(target_data) > 2 else 0)
    
    max_allowed = int(tick_income * (MAX_TRANSFER_PERCENT / 100))
    
    if max_allowed <= 0:
        await msg.reply(f"❌ Получатель не получает доход с жертв!")
        return
    
    # Проверяем дневной лимит
    today = datetime.now().strftime('%Y-%m-%d')
    await repo_biowar.cur.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM TransferLog 
        WHERE target_id = %s AND DATE(created_at) = %s
    """, (target_id, today))
    today_transfer = await repo_biowar.cur.fetchone()
    
    if isinstance(today_transfer, dict):
        already_transferred = float(today_transfer.get('COALESCE(SUM(amount), 0)', 0) or 0)
    else:
        already_transferred = float(today_transfer[0] if today_transfer else 0)
    
    remaining = max_allowed - already_transferred
    remaining = max(0, remaining)
    
    if remaining <= 0:
        await msg.reply(f"❌ Лимит на сегодня исчерпан! Осталось: 0")
        return
    
    actual_amount = min(amount, remaining)
    limit_reached = amount > remaining
    
    if actual_amount <= 0:
        await msg.reply(f"❌ Лимит превышен! Можно передать только {remaining:,}")
        return
    
    # Передаём
    await repo_biowar.cur.execute("UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s;", (actual_amount, user_id))
    await repo_biowar.cur.execute("UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s;", (actual_amount, target_id))
    
    await repo_biowar.cur.execute("""
        INSERT INTO TransferLog (sender_id, target_id, amount, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (user_id, target_id, actual_amount))
    
    await repo_biowar.cur.connection.commit()
    
    # Отправляем уведомления
    await send_transfer_notifications(msg.bot, user_id, target_id, actual_amount, msg.chat.id, msg.message_id, repo_biowar)
    
    if limit_reached:
        await msg.reply(
            f"⚠️ <b>Лимит превышен!</b>\n\n"
            f"✅ Передано: <b>{actual_amount:,}</b> (из <b>{amount:,}</b>)\n"
            f"📤 От: <code>{user_id}</code>\n"
            f"📥 Кому: <code>{target_id}</code>\n"
            f"💎 Остаток: <b>{current_resources - actual_amount:,}</b>",
            parse_mode="HTML"
        )
    else:
        await msg.reply(
            f"✅ Передано <b>{actual_amount:,}</b> ресурсов\n"
            f"📤 От: <code>{user_id}</code>\n"
            f"📥 Кому: <code>{target_id}</code>\n"
            f"💎 Остаток: <b>{current_resources - actual_amount:,}</b>",
            parse_mode="HTML"
        )


# ===== КОМАНДА ПЕРЕДАЧИ БЕЗ ЦЕЛИ (ТОЛЬКО СУММА) =====
@router.message(F.text.regexp(r'^(\.|/|!)?(отдать|передать)\s+(ресурс(ы|ов)?|рес(ы|ов)?|ресы?)\s+(\d+)$', flags=re.IGNORECASE))
async def cmd_transfer_resources_no_target(msg: Message, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    args = msg.text.split()
    
    amount = 0
    target_id = None
    
    # Ищем сумму
    for arg in args:
        if arg.isdigit():
            amount = int(arg)
            break
    
    # Проверяем реплай
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
    
    if not target_id:
        await msg.reply(
            "❌ <b>Не указана цель!</b>\n\n"
            "✅ <b>Правильно:</b>\n"
            "<code>!отдать ресы @username 100</code>\n"
            "<code>!отдать ресы</code> (реплаем) <code>100</code>\n\n"
            "📝 <b>Кому:</b> @username, @123456789, 123456789, или реплай\n"
            "🔢 <b>Сколько:</b> число больше 0",
            parse_mode="HTML"
        )
        return
    
    if target_id == user_id:
        await msg.reply("❌ Нельзя передать самому себе!")
        return
    
    if amount <= 0:
        await msg.reply("❌ Сумма должна быть больше 0!")
        return
    
    # Проверяем ресурсы отправителя
    await repo_biowar.cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await repo_biowar.cur.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return
    
    current_resources = lab[0] if isinstance(lab, (tuple, list)) else lab.get('bio_resource', 0) or 0
    
    if current_resources < amount:
        await msg.reply(f"❌ Недостаточно! У вас: <b>{current_resources:,}</b>", parse_mode="HTML")
        return
    
    # Проверяем получателя
    await repo_biowar.cur.execute("""
        SELECT l.lab_id, l.bio_resource, 
               COALESCE(SUM(v.victim_bio_resource_earn) * (1 + COALESCE(l.rebirth_level, 0) * 0.10), 0) AS tick_income
        FROM Lab l
        LEFT JOIN Victims v ON v.victims_owner_id = l.lab_id
        WHERE l.lab_id = %s
        GROUP BY l.lab_id
    """, (target_id,))
    target_data = await repo_biowar.cur.fetchone()
    
    if not target_data:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден!")
        return
    
    if isinstance(target_data, dict):
        tick_income = float(target_data.get('tick_income', 0) or 0)
    else:
        tick_income = float(target_data[2] if len(target_data) > 2 else 0)
    
    max_allowed = int(tick_income * (MAX_TRANSFER_PERCENT / 100))
    
    if max_allowed <= 0:
        await msg.reply(f"❌ Получатель не получает доход с жертв!")
        return
    
    # Проверяем дневной лимит
    today = datetime.now().strftime('%Y-%m-%d')
    await repo_biowar.cur.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM TransferLog 
        WHERE target_id = %s AND DATE(created_at) = %s
    """, (target_id, today))
    today_transfer = await repo_biowar.cur.fetchone()
    
    if isinstance(today_transfer, dict):
        already_transferred = float(today_transfer.get('COALESCE(SUM(amount), 0)', 0) or 0)
    else:
        already_transferred = float(today_transfer[0] if today_transfer else 0)
    
    remaining = max_allowed - already_transferred
    remaining = max(0, remaining)
    
    if remaining <= 0:
        await msg.reply(f"❌ Лимит на сегодня исчерпан! Осталось: 0")
        return
    
    actual_amount = min(amount, remaining)
    limit_reached = amount > remaining
    
    if actual_amount <= 0:
        await msg.reply(f"❌ Лимит превышен! Можно передать только {remaining:,}")
        return
    
    # Передаём
    await repo_biowar.cur.execute("UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s;", (actual_amount, user_id))
    await repo_biowar.cur.execute("UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s;", (actual_amount, target_id))
    
    await repo_biowar.cur.execute("""
        INSERT INTO TransferLog (sender_id, target_id, amount, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (user_id, target_id, actual_amount))
    
    await repo_biowar.cur.connection.commit()
    
    # Отправляем уведомления
    await send_transfer_notifications(msg.bot, user_id, target_id, actual_amount, msg.chat.id, msg.message_id, repo_biowar)
    
    if limit_reached:
        await msg.reply(
            f"⚠️ <b>Лимит превышен!</b>\n\n"
            f"✅ Передано: <b>{actual_amount:,}</b> (из <b>{amount:,}</b>)\n"
            f"📤 От: <code>{user_id}</code>\n"
            f"📥 Кому: <code>{target_id}</code>\n"
            f"💎 Остаток: <b>{current_resources - actual_amount:,}</b>",
            parse_mode="HTML"
        )
    else:
        await msg.reply(
            f"✅ Передано <b>{actual_amount:,}</b> ресурсов\n"
            f"📤 От: <code>{user_id}</code>\n"
            f"📥 Кому: <code>{target_id}</code>\n"
            f"💎 Остаток: <b>{current_resources - actual_amount:,}</b>",
            parse_mode="HTML"
        )


# ===== КОМАНДА ПРОВЕРКИ ЛИМИТА =====
@router.message(F.text.regexp(r'^(\.|/|!)?лимит$', flags=re.IGNORECASE))
@router.message(F.text.lower().in_(["лимит"]))
async def cmd_check_limit(msg: Message, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    target_id = None
    
    args = msg.text.split()
    
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
    else:
        for arg in args:
            if arg.startswith('@'):
                clean_arg = arg[1:]
                if clean_arg.isdigit():
                    target_id = int(clean_arg)
                else:
                    await repo_biowar.cur.execute(
                        "SELECT lab_id FROM Lab WHERE lab_id IN (SELECT id FROM Users WHERE username = %s);",
                        (clean_arg,)
                    )
                    lab = await repo_biowar.cur.fetchone()
                    if lab:
                        target_id = lab[0] if isinstance(lab, (tuple, list)) else lab.get('lab_id')
                break
            elif arg.isdigit() and len(arg) > 5:
                target_id = int(arg)
                break
    
    if not target_id:
        target_id = user_id
    
    await repo_biowar.cur.execute("""
        SELECT l.lab_id, 
               COALESCE(SUM(v.victim_bio_resource_earn) * (1 + COALESCE(l.rebirth_level, 0) * 0.10), 0) AS tick_income
        FROM Lab l
        LEFT JOIN Victims v ON v.victims_owner_id = l.lab_id
        WHERE l.lab_id = %s
        GROUP BY l.lab_id
    """, (target_id,))
    data = await repo_biowar.cur.fetchone()
    
    if not data:
        await msg.reply(f"❌ Пользователь <code>{target_id}</code> не найден!")
        return
    
    if isinstance(data, dict):
        tick_income = float(data.get('tick_income', 0) or 0)
    else:
        tick_income = float(data[1] if len(data) > 1 else 0)
    
    max_allowed = int(tick_income * (MAX_TRANSFER_PERCENT / 100))
    
    today = datetime.now().strftime('%Y-%m-%d')
    await repo_biowar.cur.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM TransferLog 
        WHERE target_id = %s AND DATE(created_at) = %s
    """, (target_id, today))
    today_data = await repo_biowar.cur.fetchone()
    
    if isinstance(today_data, dict):
        already_transferred = float(today_data.get('COALESCE(SUM(amount), 0)', 0) or 0)
    else:
        already_transferred = float(today_data[0] if today_data else 0)
    
    remaining = max_allowed - already_transferred
    remaining = max(0, remaining)
    
    name = None
    try:
        await repo_biowar.cur.execute("SELECT full_name FROM Users WHERE id = %s;", (target_id,))
        user_data = await repo_biowar.cur.fetchone()
        if user_data:
            name = user_data[0] if isinstance(user_data, (tuple, list)) else user_data.get('full_name')
    except:
        pass
    
    if not name:
        name = f"ID {target_id}"
    
    await msg.reply(
        f"📊 <b>Лимит на получение ресурсов</b>\n\n"
        f"👤 <b>Игрок:</b> {name} (<code>{target_id}</code>)\n"
        f"🧬 <b>Доход за тик:</b> <code>{tick_income:,}</code>\n"
        f"📈 <b>Максимум в день:</b> <code>{max_allowed:,}</code> (100% от дохода)\n"
        f"📤 <b>Уже получено сегодня:</b> <code>{already_transferred:,}</code>\n"
        f"💡 <b>Ещё можно получить:</b> <code>{remaining:,}</code>\n\n"
        f"⏳ <b>Обновление:</b> в 00:00",
        parse_mode="HTML"
    )


# ===== КОМАНДА ПРОВЕРКИ БАЛАНСА =====
@router.message(F.text.regexp(r'^(\.|/|!)?(баланс|ресурсы|рес|ресы?)$', flags=re.IGNORECASE))
@router.message(F.text.lower().in_(["баланс", "ресурсы", "рес", "ресы"]))
async def cmd_my_resources(msg: Message, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    
    await repo_biowar.cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await repo_biowar.cur.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return
    
    resources = lab[0] if isinstance(lab, (tuple, list)) else lab.get('bio_resource', 0) or 0
    
    await msg.reply(f"🧬 <b>Ваши ресурсы:</b> <code>{resources:,}</code>", parse_mode="HTML")


# ===== КОМАНДА ПОМОЩИ =====
@router.message(F.text.regexp(r'^(\.|/|!)?(помощь|help|команды)$', flags=re.IGNORECASE))
@router.message(F.text.lower().in_(["помощь", "help", "команды"]))
async def cmd_transfer_help(msg: Message):
    await msg.reply(
        "📚 <b>Все команды передачи ресурсов</b>\n\n"
        "✅ <b>Передать ресурсы:</b>\n"
        "<code>.отдать ресурсы @username 1000</code>\n"
        "<code>/передать ресы @id 5000</code>\n"
        "<code>!отдать ресурсы 123456789 10000</code>\n"
        "<code>.отдать ресурсы</code> (реплаем) <code>5000</code>\n\n"
        "⚠️ <b>Лимит:</b> максимум <b>100%</b> от дохода получателя за тик <b>в день</b>\n"
        "⏳ Обновление в <b>00:00</b>\n\n"
        "✅ <b>Проверить баланс:</b>\n"
        "<code>.баланс</code>\n"
        "<code>баланс</code>\n"
        "<code>!баланс</code>\n"
        "<code>/баланс</code>\n"
        "<code>.рес</code>\n"
        "<code>рес</code>\n"
        "<code>!рес</code>\n"
        "<code>/рес</code>\n\n"
        "✅ <b>Проверить лимит:</b>\n"
        "<code>.лимит</code> — свой лимит\n"
        "<code>.лимит @username</code> — лимит другого\n\n"
        "✅ <b>Помощь:</b>\n"
        "<code>.помощь</code>\n"
        "<code>помощь</code>\n"
        "<code>!помощь</code>\n"
        "<code>/помощь</code>",
        parse_mode="HTML"
    )


@router.message(F.text.regexp(r'^(\.|/|!)?(отдать|передать|баланс|ресурсы|рес|ресы?|лимит|помощь|help|команды)$', flags=re.IGNORECASE))
async def cmd_unknown(msg: Message):
    await msg.reply(
        "❌ <b>Неверный формат!</b>\n\n"
        "✅ <b>Правильно:</b>\n"
        "<code>.отдать ресурсы @username 1000</code>\n"
        "<code>/передать ресы @id 5000</code>\n"
        "<code>!отдать ресурсы 123456789 10000</code>\n"
        "<code>.отдать ресурсы</code> (реплаем) <code>5000</code>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "• <code>.баланс</code> или <code>баланс</code> — проверить ресурсы\n"
        "• <code>!баланс</code> или <code>/баланс</code> — проверить ресурсы\n"
        "• <code>.рес</code> или <code>рес</code> — проверить ресурсы\n"
        "• <code>.лимит</code> или <code>лимит</code> — проверить лимит\n"
        "• <code>.помощь</code> или <code>помощь</code> — все команды\n\n"
        "⚠️ <b>Лимит:</b> 100% от дохода получателя за тик в день",
        parse_mode="HTML"
    )

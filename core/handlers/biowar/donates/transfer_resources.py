import re
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from core.utils.db_api.repo_biowar import RequestsRepoBiowar

router = Router()

MAX_TRANSFER_PERCENT = 500  # 500% от дохода получателя за тик

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
                    result = await repo_biowar.cur.execute(
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
            "• <code>.помощь</code> или <code>помощь</code> — все команды",
            parse_mode="HTML"
        )
        return
    
    if target_id == user_id:
        await msg.reply("❌ Нельзя передать самому себе!")
        return
    
    # Проверяем ресурсы отправителя
    result = await repo_biowar.cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await repo_biowar.cur.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return
    
    current_resources = lab[0] if isinstance(lab, (tuple, list)) else lab.get('bio_resource', 0) or 0
    
    if current_resources < amount:
        await msg.reply(f"❌ Недостаточно! У вас: <b>{current_resources:,}</b>", parse_mode="HTML")
        return
    
    # Проверяем получателя и его доход за тик
    result = await repo_biowar.cur.execute("""
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
        target_resources = target_data.get('bio_resource', 0) or 0
        tick_income = float(target_data.get('tick_income', 0) or 0)
    else:
        target_resources = target_data[1] if len(target_data) > 1 else 0
        tick_income = float(target_data[2] if len(target_data) > 2 else 0)
    
    # ЕЖЕДНЕВНЫЙ ЛИМИТ: 500% от дохода получателя за тик
    max_allowed = int(tick_income * (MAX_TRANSFER_PERCENT / 100))
    
    if max_allowed <= 0:
        await msg.reply(
            f"❌ <b>Получатель не получает доход с жертв!</b>\n\n"
            f"🧬 Доход за тик: <b>{tick_income:,}</b>\n"
            f"📈 Максимум можно передать: <b>{max_allowed:,}</b> (500% от дохода)\n"
            f"📤 Вы пытались передать: <b>{amount:,}</b>",
            parse_mode="HTML"
        )
        return
    
    # Проверяем, сколько уже передано сегодня получателю
    today = datetime.now().strftime('%Y-%m-%d')
    result = await repo_biowar.cur.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM TransferLog 
        WHERE target_id = %s AND DATE(created_at) = %s
    """, (target_id, today))
    today_transfer = await repo_biowar.cur.fetchone()
    
    if isinstance(today_transfer, dict):
        already_transferred = float(today_transfer.get('COALESCE(SUM(amount), 0)', 0) or 0)
    else:
        already_transferred = float(today_transfer[0] if today_transfer else 0)
    
    remaining = max_allowed - already_transferred
    
    if remaining <= 0:
        await msg.reply(
            f"❌ <b>Лимит на сегодня исчерпан!</b>\n\n"
            f"🧬 Доход получателя за тик: <b>{tick_income:,}</b>\n"
            f"📈 Лимит на день: <b>{max_allowed:,}</b> (500% от дохода)\n"
            f"📤 Уже передано сегодня: <b>{already_transferred:,}</b>\n"
            f"❌ Осталось: <b>0</b>\n\n"
            f"⏳ Следующее обновление в <b>00:00</b>",
            parse_mode="HTML"
        )
        return
    
    actual_amount = amount
    limit_reached = False
    
    if amount > remaining:
        actual_amount = int(remaining)
        limit_reached = True
    
    if actual_amount <= 0:
        await msg.reply(
            f"❌ <b>Лимит превышен!</b>\n\n"
            f"🧬 Доход получателя за тик: <b>{tick_income:,}</b>\n"
            f"📈 Лимит на день: <b>{max_allowed:,}</b> (500% от дохода)\n"
            f"📤 Уже передано сегодня: <b>{already_transferred:,}</b>\n"
            f"💡 Осталось: <b>{remaining:,}</b>",
            parse_mode="HTML"
        )
        return
    
    # Передаём
    await repo_biowar.cur.execute("UPDATE Lab SET bio_resource = bio_resource - %s WHERE lab_id = %s;", (actual_amount, user_id))
    await repo_biowar.cur.execute("UPDATE Lab SET bio_resource = bio_resource + %s WHERE lab_id = %s;", (actual_amount, target_id))
    
    # Логируем передачу
    await repo_biowar.cur.execute("""
        INSERT INTO TransferLog (sender_id, target_id, amount, created_at)
        VALUES (%s, %s, %s, NOW())
    """, (user_id, target_id, actual_amount))
    
    await repo_biowar.cur.connection.commit()
    
    if limit_reached:
        await msg.reply(
            f"⚠️ <b>Лимит превышен!</b>\n\n"
            f"✅ Передано: <b>{actual_amount:,}</b> ресурсов (из <b>{amount:,}</b> запрошенных)\n"
            f"📤 От: <code>{user_id}</code>\n"
            f"📥 Кому: <code>{target_id}</code>\n"
            f"🧬 Доход получателя за тик: <b>{tick_income:,}</b>\n"
            f"📈 Лимит на день: <b>{max_allowed:,}</b> (500% от дохода)\n"
            f"📤 Передано сегодня: <b>{already_transferred + actual_amount:,}</b>\n"
            f"💎 Остаток у вас: <b>{current_resources - actual_amount:,}</b>",
            parse_mode="HTML"
        )
    else:
        await msg.reply(
            f"✅ Передано <b>{actual_amount:,}</b> ресурсов\n"
            f"📤 От: <code>{user_id}</code>\n"
            f"📥 Кому: <code>{target_id}</code>\n"
            f"📤 Передано сегодня: <b>{already_transferred + actual_amount:,}</b>\n"
            f"💎 Остаток у вас: <b>{current_resources - actual_amount:,}</b>",
            parse_mode="HTML"
        )


@router.message(F.text.regexp(r'^(\.|/|!)?(баланс|ресурсы|рес|ресы?)$', flags=re.IGNORECASE))
@router.message(F.text.lower().in_(["баланс", "ресурсы", "рес", "ресы"]))
async def cmd_my_resources(msg: Message, repo_biowar: RequestsRepoBiowar):
    user_id = msg.from_user.id
    
    result = await repo_biowar.cur.execute("SELECT bio_resource FROM Lab WHERE lab_id = %s;", (user_id,))
    lab = await repo_biowar.cur.fetchone()
    
    if not lab:
        await msg.reply("❌ У вас нет лаборатории!")
        return
    
    resources = lab[0] if isinstance(lab, (tuple, list)) else lab.get('bio_resource', 0) or 0
    
    await msg.reply(f"🧬 <b>Ваши ресурсы:</b> <code>{resources:,}</code>", parse_mode="HTML")


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
        "⚠️ <b>Лимит:</b> максимум <b>500%</b> от дохода получателя за тик <b>в день</b>\n"
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
        "✅ <b>Помощь:</b>\n"
        "<code>.помощь</code>\n"
        "<code>помощь</code>\n"
        "<code>!помощь</code>\n"
        "<code>/помощь</code>",
        parse_mode="HTML"
    )


@router.message(F.text.regexp(r'^(\.|/|!)?(отдать|передать|баланс|ресурсы|рес|ресы?|помощь|help|команды)$', flags=re.IGNORECASE))
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
        "• <code>.помощь</code> или <code>помощь</code> — все команды\n\n"
        "⚠️ <b>Лимит:</b> 500% от дохода получателя за тик в день",
        parse_mode="HTML"
    )

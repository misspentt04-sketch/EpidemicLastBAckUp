import datetime

REPORT_CHAT_ID = -1003688648228  # Замените при необходимости на ID вашего основного чата/канала

async def send_weekly_top_report(bot):
    try:
        from core.handlers.biowar.admin.infection_top import get_top_text
        top_text = await get_top_text("w")
        report_msg = (
            "📊 <b>Итоги недели! Топ по заражениям</b>\n\n"
            f"{top_text}\n\n"
            "🎉 Поздравляем победителей недели!"
        )
        await bot.send_message(REPORT_CHAT_ID, report_msg, parse_mode="HTML")
        print("✅ Еженедельный отчет по заражениям успешно отправлен!")
    except Exception as e:
        print(f"❌ Ошибка отправки еженедельного отчета: {e}")

async def send_monthly_top_report(bot):
    try:
        from core.handlers.biowar.admin.infection_top import get_top_text
        top_text = await get_top_text("m")
        report_msg = (
            "📆 <b>Итоги месяца! Топ по заражениям</b>\n\n"
            f"{top_text}\n\n"
            "🏆 Отличная работа за месяц!"
        )
        await bot.send_message(REPORT_CHAT_ID, report_msg, parse_mode="HTML")
        print("✅ Ежемесячный отчет по заражениям успешно отправлен!")
    except Exception as e:
        print(f"❌ Ошибка отправки ежемесячного отчета: {e}")

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from core.services.loop_tasks import force_tick

router = Router()

# Глобальный пул (будет установлен при старте)
_pool = None

def set_pool(pool):
    global _pool
    _pool = pool

# ===== КОМАНДА !ТИК =====
@router.message(F.text.lower().startswith("!тик"))
async def cmd_force_tick(msg: types.Message):
    user_id = msg.from_user.id

    if user_id != 7972320837:
        await msg.reply("❌ У вас нет прав на эту команду!")
        return

    if not _pool:
        await msg.reply("❌ Ошибка: пул подключений не инициализирован!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, выполнить тик", callback_data="confirm_tick_yes"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="confirm_tick_no")
        ]
    ])

    await msg.reply(
        "⚠️ <b>Вы уверены?</b>\n\n"
        "Вы собираетесь выполнить принудительный тик.\n"
        "Всем игрокам будут начислены био-ресурсы за жертв.\n\n"
        "Подтвердите действие:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ===== ПОДТВЕРЖДЕНИЕ =====
@router.callback_query(F.data.startswith("confirm_tick_"))
async def confirm_force_tick(call: CallbackQuery):
    action = call.data.split("_")[-1]
    user_id = call.from_user.id

    if user_id != 7972320837:
        await call.answer("❌ Это не ваша кнопка!", show_alert=True)
        return

    if not _pool:
        await call.message.edit_text("❌ Ошибка: пул подключений не инициализирован!")
        return

    if action == "no":
        await call.message.edit_text("❌ Тик отменён.")
        await call.answer()
        return

    if action == "yes":
        await call.message.edit_text("⏳ Выполняю тик...")
        await call.answer()

        try:
            await force_tick(_pool)
            await call.message.edit_text(
                "✅ <b>Тик успешно выполнен!</b>\n\n"
                "Всем игрокам начислены био-ресурсы за жертв.",
                parse_mode="HTML"
            )
        except Exception as e:
            await call.message.edit_text(f"❌ Ошибка при выполнении тика: {e}")

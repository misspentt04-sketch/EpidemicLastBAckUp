import math
import logging
from aiogram import Router, F, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import func

router = Router()
logger = logging.getLogger(__name__)

SKILL_MAP = {
    "infect": "🎯 Заразность",
    "immunity": "🛡 Иммунитет",
    "lethality": "☠️ Летальность",
    "security_service": "🔒 Безопасность",
    "science": "🧪 Разработка",
    "pathogens": "🧬 Патогены",
}


class CalcStates(StatesGroup):
    waiting_levels = State()
    waiting_expr = State()


def _main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 ЗЗ", callback_data="calc_skill:infect"),
         InlineKeyboardButton(text="🛡 Иммун", callback_data="calc_skill:immunity")],
        [InlineKeyboardButton(text="☠️ Летал", callback_data="calc_skill:lethality"),
         InlineKeyboardButton(text="🔒 СБ", callback_data="calc_skill:security_service")],
        [InlineKeyboardButton(text="🧪 Разраб", callback_data="calc_skill:science"),
         InlineKeyboardButton(text="🧬 Патогены", callback_data="calc_skill:pathogens")],
        [InlineKeyboardButton(text="🧮 Обычный калькулятор", callback_data="calc_regular")],
    ])


def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="calc_cancel")],
    ])


@router.message(F.text.lower().in_({
    "!кальк", ".кальк", "/кальк", "кальк",
    "!калькулятор", ".калькулятор", "/калькулятор", "калькулятор",
}))
async def cmd_calc(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🧮 <b>Калькулятор</b>\n\n"
        "Выбери отдел для прокачки:\n\n"
        "<i>👇 Или нажми «Обычный калькулятор»</i>",
        parse_mode="HTML",
        reply_markup=_main_menu(),
    )


@router.callback_query(F.data == "calc_cancel")
async def on_cancel(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer("Отменено")


@router.callback_query(F.data.startswith("calc_skill:"))
async def on_skill(call: types.CallbackQuery, state: FSMContext):
    skill = call.data.split(":")[1]
    if skill not in SKILL_MAP:
        return await call.answer("❌ Неизвестный отдел", show_alert=True)

    await state.set_state(CalcStates.waiting_levels)
    await state.update_data(skill=skill)

    try:
        await call.message.edit_text(
            f"🧮 <b>Калькулятор: {SKILL_MAP[skill]}</b>\n\n"
            f"📊 Введи: <b>с_какого_уровня до_какого</b>\n"
            f"   Пример: <code>100 105</code>",
            parse_mode="HTML",
            reply_markup=_cancel_kb(),
        )
    except Exception:
        pass
    await call.answer()


@router.message(CalcStates.waiting_levels)
async def on_levels(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    skill = data.get("skill")
    if not skill:
        await state.clear()
        return await msg.answer("❌ Ошибка, начни заново: <code>!кальк</code>", parse_mode="HTML")

    parts = (msg.text or "").strip().split()
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return await msg.answer(
            "❌ Формат: <code>100 5</code> — два числа через пробел.\n"
            "Попробуй ещё раз или нажми «Отмена».",
            parse_mode="HTML",
            reply_markup=_cancel_kb(),
        )

    from_lvl = int(parts[0])
    to_lvl = int(parts[1])

    if to_lvl <= from_lvl:
        return await msg.answer("❌ Второе число должно быть больше первого.")
    if to_lvl - from_lvl > 1000:
        return await msg.answer("❌ Максимум 1000 уровней за раз.")

    base = func.lvl_up_calc(skill, from_lvl, to_lvl)

    lines = [
        f"🧮 <b>{SKILL_MAP[skill]}</b>: <code>{from_lvl}</code> → <code>{to_lvl}</code>",
        "",
        "💰 <b>Стоимость по уровням РБ:</b>",
    ]

    for rb in range(0, 5):
        discount = min(rb * 0.025, 0.10)
        price = int(base * (1 - discount))
        if rb == 0:
            lines.append(f"• Без РБ: <code>{price:,}</code> 🧬")
        else:
            pct = rb * 2.5
            lines.append(f"• РБ {rb} (−{pct:g}%): <code>{price:,}</code> 🧬")

    lines.append("")
    lines.append(f"<i>Базовая цена: {base:,} 🧬</i>")

    await msg.answer("\n".join(lines), parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "calc_regular")
async def on_regular(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CalcStates.waiting_expr)
    try:
        await call.message.edit_text(
            "🧮 <b>Обычный калькулятор</b>\n\n"
            "Введи выражение или уравнение:\n\n"
            "• Арифметика: <code>2+2*10</code>\n"
            "• Функции: <code>sqrt(16) + 3^2</code>\n"
            "• Уравнение: <code>x^2 + 5 = 14</code>",
            parse_mode="HTML",
            reply_markup=_cancel_kb(),
        )
    except Exception:
        pass
    await call.answer()


@router.message(CalcStates.waiting_expr)
async def on_expr(msg: types.Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text:
        return await msg.answer("❌ Пустой ввод. Попробуй ещё раз.")

    try:
        if "=" in text:
            import sympy
            from sympy.parsing.sympy_parser import (
                parse_expr, standard_transformations, implicit_multiplication_application,
            )
            transformations = standard_transformations + (implicit_multiplication_application,)

            left, right = text.split("=", 1)
            left = left.replace("^", "**")
            right = right.replace("^", "**")

            x = sympy.Symbol("x")
            eq = sympy.Eq(
                parse_expr(left, transformations=transformations, evaluate=True),
                parse_expr(right, transformations=transformations, evaluate=True),
            )
            solutions = sympy.solve(eq, x)
            if not solutions:
                return await msg.answer("❌ Решений нет.")

            sol_str = ", ".join(f"<code>{s}</code>" for s in solutions)
            return await msg.answer(f"🧮 <b>Решение:</b> x = {sol_str}", parse_mode="HTML")
        else:
            expr = text.replace("^", "**")
            allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            allowed.update({
                "abs": abs, "round": round, "min": min, "max": max,
                "pow": pow, "int": int, "float": float,
            })
            result = eval(expr, {"__builtins__": {}}, allowed)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return await msg.answer(f"🧮 <b>Результат:</b> <code>{result}</code>", parse_mode="HTML")
    except Exception as e:
        return await msg.answer(f"❌ Ошибка: <code>{e}</code>", parse_mode="HTML")
    finally:
        await state.clear()

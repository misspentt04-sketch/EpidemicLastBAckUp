path = "core/handlers/biowar/infects/infect.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Находим и меняем блок формирования текста для темы
old_code = """    custom_success_template = await get_theme_text(db, infecter['id'], "infect_success", None)
    if custom_success_template:
        res_gain_str = f"\\n✨ Бизнесмен согласился платить за крышу! Это пополнило кассу синдиката за счёт регулярных отчислений: +{intcomma(earn_exp)} к чёрному безналу" if vic_new else ""
        text = custom_success_template.format(
            attacker_mention=inf_entity,
            target_mention=vic_entity,
            pathogen_name=infecter['pathogen_name'] if infecter['pathogen_name'] else "Неизвестное дело",
            fever_time=fever_time_,
            expire_days=infecter["lethality"],
            exp_gain=intcomma(earn_exp),
            res_gain=res_gain_str,
            victim_new=res_gain_str
        )
    else:
        text = default_success_msg"""

new_code = """    custom_success_template = await get_theme_text(db, infecter['id'], "infect_success", None)
    if custom_success_template:
        if vic_new:
            res_gain_str = intcomma(earn_exp)
            text = custom_success_template.format(
                attacker_mention=inf_entity,
                target_mention=vic_entity,
                pathogen_name=infecter['pathogen_name'] if infecter['pathogen_name'] else "Неизвестное дело",
                fever_time=fever_time_,
                expire_days=infecter["lethality"],
                exp_gain=intcomma(earn_exp),
                res_gain=res_gain_str,
                victim_new=res_gain_str
            )
        else:
            # Если жертва повторная, убираем статичную строку бизнесмена из шаблона темы
            res_gain_str = ""
            text = custom_success_template.format(
                attacker_mention=inf_entity,
                target_mention=vic_entity,
                pathogen_name=infecter['pathogen_name'] if infecter['pathogen_name'] else "Неизвестное дело",
                fever_time=fever_time_,
                expire_days=infecter["lethality"],
                exp_gain=intcomma(earn_exp),
                res_gain="",
                victim_new=""
            )
            # Очищаем возможные обрезки строк темы, если там зашит статичный текст про бизнесмена
            import re
            text = re.sub(r'\\n?✨\\s*Бизнесмен согласился платить за крышу!.*?(безналу|кассу)?', '', text, flags=re.DOTALL)
    else:
        text = default_success_msg"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Вырезание строки для старых жертв в темах успешно настроено!")
else:
    print("⚠️ Старый блок не найден. Выполняем гибкую замену...")
    # Альтернативная точечная замена
    lines = content.splitlines()
    fixed_lines = []
    for line in lines:
        fixed_lines.append(line)
        if "custom_success_template = await get_theme_text" in line:
            pass
    # Применяем патч через регулярные выражения
    pattern = r'custom_success_template = await get_theme_text\(db, infecter\[\'id\'\], "infect_success", None\).*?else:\s+text = default_success_msg'
    import re
    if re.search(pattern, content, flags=re.DOTALL):
        content = re.sub(pattern, new_code, content, flags=re.DOTALL)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ Гибкая замена выполнена!")
    else:
        print("❌ Не удалось найти блок для замены.")

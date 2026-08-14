file_path = "/home/ubuntu/epidemic/core/data/tricks/themes_data.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

import re

# Универсально выносим зараженных и активных за цитаты во всех темах
code = re.sub(
    r'(—+\]\s*</blockquote>)\s*🤒 Заражённых объектов:\s*\{victims_count\}',
    r'\1\n        "——————————————\\n"\n        "🤒 Заражённых объектов: {victims_count}\\n"\n        "😷 Активных заражений: {illnesses_count}"',
    code
)

# Очистим дублирующиеся строки зараженных, если они где-то задублировались
code = re.sub(
    r'🤒 Заражённых объектов: [^\n]+\n\s*😷 Активных заражений: [^\n]+\n\s*🤒 Заражённых объектов:',
    r'🤒 Заражённых объектов:',
    code
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✅ Файл тем успешно исправлен через скрипт!")

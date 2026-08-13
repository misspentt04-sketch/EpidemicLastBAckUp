import re
import os

EXCLUDED_IDS = (8236324289, 7754333998, 7972320837)
EXCLUDED_STR = ", ".join(map(str, EXCLUDED_IDS))

# Добавляем пользователей в специальную таблицу исключений юзербота, если она используется
import subprocess
try:
    for uid in EXCLUDED_IDS:
        cmd = f"mysql -u root -p1603 epidemic -e \"INSERT IGNORE INTO ub_exceptions (user_id) VALUES ({uid});\" 2>/dev/null"
        subprocess.run(cmd, shell=True)
except Exception:
    pass

print(f"Исключённые ID: {EXCLUDED_STR}")

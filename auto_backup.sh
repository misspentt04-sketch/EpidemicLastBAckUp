#!/bin/bash

# Конфигурация
DB_USER="root"
DB_PASS="1603"
DB_NAME="epidemic"
BOT_TOKEN="8879844317:AAG6vbTP1przGNtB5qUW5LAhAXVVDRnLPGo"
CHAT_ID="7972320837"

# Имя файла бэкапа
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="/tmp/epidemic_db_${TIMESTAMP}.sql.gz"

# ID последнего сообщения с бэкапом (файл для хранения)
LAST_MSG_FILE="/tmp/last_backup_msg_id.txt"

# ===== УДАЛЯЕМ ПРЕДЫДУЩИЙ БЭКАП =====
if [ -f "$LAST_MSG_FILE" ]; then
    LAST_MSG_ID=$(cat "$LAST_MSG_FILE")
    if [ -n "$LAST_MSG_ID" ]; then
        curl -s -X POST \
            "https://api.telegram.org/bot${BOT_TOKEN}/deleteMessage" \
            -d "chat_id=${CHAT_ID}" \
            -d "message_id=${LAST_MSG_ID}" > /dev/null
        echo "[$(date)] Удалён старый бэкап (msg_id=$LAST_MSG_ID)"
    fi
fi

# ===== СОЗДАНИЕ СЖАТОГО ДАМПА БД =====
mysqldump -u "${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

# ===== ОТПРАВКА =====
RESPONSE=$(curl -s -F document=@"${BACKUP_FILE}" \
     -F caption="📦 <b>Автобэкап базы данных</b> <code>${DB_NAME}</code> от ${TIMESTAMP}" \
     -F parse_mode="HTML" \
     "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument?chat_id=${CHAT_ID}")

# ===== СОХРАНЯЕМ ID НОВОГО СООБЩЕНИЯ =====
NEW_MSG_ID=$(echo "$RESPONSE" | grep -o '"message_id":[0-9]*' | head -1 | cut -d':' -f2)
if [ -n "$NEW_MSG_ID" ]; then
    echo "$NEW_MSG_ID" > "$LAST_MSG_FILE"
    echo "[$(date)] Отправлен новый бэкап (msg_id=$NEW_MSG_ID)"
else
    echo "[$(date)] Ошибка отправки: $RESPONSE"
fi

# ===== УДАЛЕНИЕ ВРЕМЕННОГО ФАЙЛА =====
rm -f "${BACKUP_FILE}"

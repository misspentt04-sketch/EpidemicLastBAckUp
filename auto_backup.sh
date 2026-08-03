#!/bin/bash

# Конфигурация
DB_USER="root"
DB_PASS="1603"
DB_NAME="epidemic"
BOT_TOKEN="8879844317:AAEtxKO3Aq-ZkKxDLULBP9QZ6-o6w1g8NJA"
CHAT_ID="-1003688648228"

# Имя файла бэкапа
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="/tmp/epidemic_db_${TIMESTAMP}.sql.gz"

# Создание сжатого дампа БД
mysqldump -u "${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

# Отправка файла в Telegram
curl -s -F document=@"${BACKUP_FILE}" \
     -F caption="📦 <b>Автобэкап базы данных</b> <code>${DB_NAME}</code> от ${TIMESTAMP}" \
     -F parse_mode="HTML" \
     "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument?chat_id=${CHAT_ID}" > /dev/null

# Удаление временного файла из системы
rm -f "${BACKUP_FILE}"

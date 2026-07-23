# Эпидемик: Био-Войны

`Эпидемик: Био-Войны` — игровая Telegram-система про вирусы, лаборатории, заражения, корпорации, питомцев, браки, события и донатные механики. Игровая логика работает в Python-приложении на aiogram, а отдельные фоновые/вспомогательные задачи вынесены в Go-сервис `buster/`.

Telegram-канал игры: https://t.me/epidemic_news

## Требования

- Python 3.12
- Poetry
- Redis
- MySQL или MariaDB
- Go 1.20+ для опционального сервиса `buster`

## Конфигурация

Секреты и runtime-настройки читаются из локального файла `input`. Этот файл игнорируется Git и не должен попадать в репозиторий.

Создайте его из шаблона:

```bash
cp input.example input
```

Пример:

```dotenv
TOKEN=replace_with_telegram_bot_token
ADMIN_ID=777000
ADMIN_CHAT_ID=-777000
BOT_ID=777000
BOT_USERNAME=my_bot
ip=localhost
db=epidemic
user=epic
password=change_me
REDIS_IP=localhost
CRYPTO_BOT_TOKEN=
GENAI_API_KEY=
CHAT_LOGS=-777000
CHAT_ADMINS=-777000
```

Поля:

- `TOKEN`: токен Telegram-бота из BotFather.
- `ADMIN_ID`: ID администраторов Telegram через запятую.
- `ADMIN_CHAT_ID`: ID админ-чата.
- `BOT_ID`: Telegram ID бота.
- `BOT_USERNAME`: username бота без `@`.
- `ip`, `db`, `user`, `password`: настройки подключения к MySQL для Python-приложения.
- `REDIS_IP`: хост Redis.
- `CRYPTO_BOT_TOKEN`: токен CryptoBot, нужен только для крипто-платежей.
- `GENAI_API_KEY`: ключ Google Generative AI, нужен только для GenAI-функций.
- `CHAT_LOGS`, `CHAT_ADMINS`: ID чатов для логов и модерации.

## MySQL И Redis

Запустите Redis и MySQL локально, затем создайте базу и пользователя, которые указаны в `input`.

Пример настройки MySQL:

```sql
CREATE DATABASE epidemic CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'epic'@'localhost' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON epidemic.* TO 'epic'@'localhost';
FLUSH PRIVILEGES;
```

Python-приложение само создаёт и обновляет свои таблицы при запуске через `core/utils/db_api/create_database.py`.

## Установка Зависимостей Python

```bash
poetry install
```

Если Poetry не установлен:

```bash
python3 -m pip install --user pipx
pipx install poetry
```

## Запуск Бота

```bash
poetry run python app.py
```

Ожидаемый вывод при успешном запуске:

```text
Started succesfully!
```

Бот работает через long polling и при старте сбрасывает накопленные pending updates.

## Запуск Buster

Go-сервис читает настройки MySQL из переменных окружения:

- `MYSQL_HOST`, по умолчанию `localhost`
- `MYSQL_USER`, по умолчанию `epidemic`
- `MYSQL_PASSWORD`, без значения по умолчанию
- `MYSQL_DATABASE`, по умолчанию `epidemic`

Запуск:

```bash
cd buster
MYSQL_HOST=localhost \
MYSQL_USER=epic \
MYSQL_PASSWORD=change_me \
MYSQL_DATABASE=epidemic \
go run .
```

Сборка локального бинарника:

```bash
cd buster
go build -o go_buster .
```

`go_buster` игнорируется Git.

## Полезные Проверки

```bash
python3 -m py_compile $(git ls-files '*.py')
cd buster && go test ./...
```

## Решение Частых Проблем

- `File not found: input`: создайте `input` из `input.example`.
- Ошибка подключения к MySQL: проверьте `ip`, `db`, `user` и `password` в `input`.
- Ошибка подключения к Redis: проверьте `REDIS_IP` и что Redis слушает порт `6379`.
- Не работают платежи: проверьте `CRYPTO_BOT_TOKEN`.
- Не работают GenAI-функции: проверьте `GENAI_API_KEY`.

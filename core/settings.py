from environs import Env
from dataclasses import dataclass

from pytz import timezone

@dataclass
class Bots:
    bot_token: str
    admin_id: list[str]
    admin_chat_id: int
    bot_id: int
    bot_username: str
    chat_logs_id: int
    chat_admins_id: int

@dataclass 
class DB:
    ip: str
    db: str
    password: str
    user: str

@dataclass
class RedisDB:
    ip: str

@dataclass
class CryptoBot:
    token: str

@dataclass
class GenAI:
    api_key: str

@dataclass
class Settings:
    bots: Bots
    db: DB
    redis: RedisDB
    crypto_bot: CryptoBot
    genai: GenAI


def get_settings(path: str):
    env = Env()
    env.read_env(path)
    admin_chat_id = env.int('ADMIN_CHAT_ID')
    return Settings(
        bots=Bots(
            bot_token=env.str('TOKEN'),
            admin_id=env.list('ADMIN_ID'),
            admin_chat_id=admin_chat_id,
            bot_id=env.int('BOT_ID'),
            bot_username=env.str('BOT_USERNAME'),
            chat_logs_id=env.int('CHAT_LOGS', default=admin_chat_id),
            chat_admins_id=env.int('CHAT_ADMINS', default=admin_chat_id)
        ),
        db=DB(
            ip=env.str('ip'),
            db=env.str('db'),
            user=env.str('user'),
            password=env.str('password')
        ),
        redis=RedisDB(
            ip=env.str('REDIS_IP')
        ),
        crypto_bot=CryptoBot(
            token=env.str('CRYPTO_BOT_TOKEN')
        ),
        genai=GenAI(
            api_key=env.str('GENAI_API_KEY')
        )
    )


settings = get_settings('input')

CHAT_LOGS = settings.bots.chat_logs_id
CHAT_ADMINS = settings.bots.chat_admins_id

admin_names = {}

moscow_tz = timezone('Europe/Moscow')

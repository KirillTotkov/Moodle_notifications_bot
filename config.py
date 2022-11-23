import logging
import os
from aiogram.dispatcher.dispatcher import log

from dotenv import load_dotenv

load_dotenv()

MOODLE_HOST = os.getenv("MOODLE_HOST")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ADMIN_ID = int(os.getenv("BOT_ADMIN_ID"))
DATABASE_URL = f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:' \
               f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}/' \
               f'{os.getenv("POSTGRES_DB")}'


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.FileHandler(f'../logs/{name}.log', encoding='utf-8'))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.handlers[0].setFormatter(formatter)
    return logger


bot_loger = get_logger('bot')
moodle_loger = get_logger('moodle')
scheduler_loger = get_logger('scheduler')
db_loger = get_logger('db')

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 '
}

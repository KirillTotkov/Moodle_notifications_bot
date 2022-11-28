import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.dispatcher.dispatcher import log as bot_logger

from dotenv import load_dotenv

load_dotenv()

MOODLE_HOST = os.getenv("MOODLE_HOST")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ADMIN_ID = int(os.getenv("BOT_ADMIN_ID"))
DATABASE_URL = f'postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:' \
               f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}/' \
               f'{os.getenv("POSTGRES_DB")}'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
scheduler = AsyncIOScheduler()


def set_settings_logger(logger, name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, 'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    logger.addHandler(logging.FileHandler(os.path.join(log_dir, f'{name}.log')))
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.handlers[0].setFormatter(formatter)


set_settings_logger(bot_logger, 'bot')

moodle_loger = logging.getLogger('moodle')
set_settings_logger(moodle_loger, 'moodle')

scheduler_loger = logging.getLogger('apscheduler.scheduler')
set_settings_logger(scheduler_loger, 'scheduler')

db_loger = logging.getLogger('sqlalchemy.engine')
set_settings_logger(db_loger, 'db')

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 '
}

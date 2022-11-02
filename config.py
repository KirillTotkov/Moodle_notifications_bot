import logging
import os
from aiogram.dispatcher.dispatcher import log

from dotenv import load_dotenv

load_dotenv()

# MOODLE_HOST = os.getenv("MOODLE_HOST")
MOODLE_HOST = os.getenv("TEST_MOODLE_HOST")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ADMIN_ID = int(os.getenv("BOT_ADMIN_ID"))
# ADMIN_MOODLE_TOKEN = os.getenv("ADMIN_MOODLE_TOKEN")
ADMIN_MOODLE_TOKEN = os.getenv("TEST_ADMIN_MOODLE_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL_SQLITE")

token = 'e37848688ca30f5d49893f42ef159086'

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

bot_loger = log
bot_loger.setLevel(logging.INFO)
bot_loger.addHandler(logging.FileHandler('./../logs/bot.log', encoding='utf-8'))
bot_loger.handlers[0].setFormatter(formatter)

moodle_loger = logging.getLogger('moodle')
moodle_loger.setLevel(logging.INFO)
moodle_loger.addHandler(logging.FileHandler('../logs/moodle.log', encoding='utf-8'))
moodle_loger.handlers[0].setFormatter(formatter)

scheduler_loger = logging.getLogger('apscheduler.scheduler')
scheduler_loger.setLevel(logging.INFO)
scheduler_loger.addHandler(logging.FileHandler('../logs/scheduler.log', encoding='utf-8'))
scheduler_loger.handlers[0].setFormatter(formatter)

db_loger = logging.getLogger('sqlalchemy.engine')
db_loger.setLevel(logging.INFO)
db_loger.addHandler(logging.FileHandler('../logs/db.log', encoding='utf-8'))
db_loger.handlers[0].setFormatter(formatter)

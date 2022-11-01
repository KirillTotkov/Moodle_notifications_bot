import time

from aiogram import executor

from create_bot import dp


def run():
    executor.start_polling(dp)


if __name__ == "__main__":
    run()

import time

from aiogram import executor
from aiogram.utils.exceptions import BotBlocked

from config import dp, scheduler, bot_logger, moodle_loger
from bot.handlers import user as user_handlers
from bot.handlers import admin as admin_handlers
from db.models import User
from bot.handlers.user import send_new_tasks_and_courses


@scheduler.scheduled_job('interval', seconds=1600, id='tasks')
async def main():
    start = time.time()

    all_users = await User.get_all()

    "Получение заданий для всех пользователей и отправка уведомлений"
    all_tasks = set()
    for user in all_users:
        try:
            tasks = await send_new_tasks_and_courses(user)
            all_tasks.update(tasks)
        except BotBlocked:
            bot_logger.info(f"Бот заблокирован пользователем {user}")
            await user.remove_courses()
            await user.delete()

    "Добавление новых заданий и обсуждений в БД"
    for task_discussion in all_tasks:
        await task_discussion.save()

    moodle_loger.info(f'Количество новых заданий: {len(all_tasks)}')
    moodle_loger.info(f'Время получения и отправки заданий: {time.time() - start} секунд')

    print(f'Time: {time.time() - start}')


async def on_startup(dispatcher):
    print('Запуск бота')
    bot_logger.info("Запуск бота")

    scheduler.start()
    await user_handlers.register_handlers(dispatcher)
    await admin_handlers.register_handlers(dispatcher)


async def on_shutdown(dispatcher):
    print('Остановка бота')
    bot_logger.info("Остановка бота")

    scheduler.shutdown()
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)

import time

from aiogram import executor
from aiogram.utils.exceptions import BotBlocked

from config import dp, bot, scheduler, bot_logger, moodle_loger, BOT_ADMIN_ID
from handlers import user as user_handlers, admin as admin_handlers
from db.models import User
from handlers.user import send_new_tasks_and_courses
from moodle.courses import TokenException


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
            bot_logger.exception(f"Бот заблокирован пользователем {user}")
            await user.delete()
        except TokenException:
            await bot.send_message(user.id, f'Произошла ошибка. \n'
                                            f'Вам необходимо заново авторизоваться в боте. \n'
                                            f'<b>Для этого введите команду /start</b>', parse_mode='HTML')
            await user.delete()
            await bot.send_message(BOT_ADMIN_ID, f'У пользователя {user.id} - @{user.username} недействительный токен')

    "Добавление новых заданий и обсуждений в БД"
    for task_discussion in all_tasks:
        await task_discussion.save()

    moodle_loger.info(f'Количество новых заданий: {len(all_tasks)}')
    moodle_loger.info(f'Время получения и отправки заданий: {time.time() - start} секунд')


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

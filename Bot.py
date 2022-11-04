import asyncio
import time

from aiogram import executor

from bot.create_bot import dp, scheduler
from bot.handlers import user as user_handlers
from bot.handlers import admin as admin_handlers
from db.models import User
from moodle.discussions import get_new_discussions
from bot.handlers.user import send_tasks_to_user
from config import bot_loger
from moodle.tasks import get_new_tasks
from db.base import init_db, get_session
from moodle.courses import get_new_courses


async def get_user_tasks(user: User):
    "Получение заданий для каждого курса"
    async_tasks = []
    for course in user.courses:
        async_tasks.append(get_new_tasks(user.moodle_token, course))
        async_tasks.append(get_new_discussions(user.moodle_token, course))

    all_tasks_discussions = await asyncio.gather(*async_tasks)
    all_tasks_discussions = [task for user_tasks in all_tasks_discussions for task in user_tasks]

    new_courses = await get_new_courses(user)
    if new_courses:
        await user.add_courses(new_courses)
        await send_tasks_to_user(user.id, new_courses)

    "Отправка уведомлений"
    await send_tasks_to_user(user.id, all_tasks_discussions)

    return all_tasks_discussions


@scheduler.scheduled_job('interval', seconds=60, id='get_user_tasks')
async def main():
    start = time.time()

    all_users = await User.get_all()

    "Получение заданий для всех пользователей и отправка уведомлений"
    async_tasks = []
    for user in all_users:
        async_tasks.append(get_user_tasks(user))

    all_tasks = await asyncio.gather(*async_tasks)
    all_tasks = {task for user_tasks in all_tasks for task in user_tasks}

    "Добавление новых заданий и обсуждений в БД"
    for task_discussion in all_tasks:
        await task_discussion.create()

    print(f'Time: {time.time() - start}')


async def on_startup(dispatcher):
    # await init_db()
    scheduler.start()
    await user_handlers.register_handlers(dispatcher)
    await admin_handlers.register_handlers(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)

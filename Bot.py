import asyncio
import time
from pprint import pprint
from typing import NamedTuple

import aiohttp
from aiogram import executor
from aiogram.utils.exceptions import RetryAfter

from bot.create_bot import dp, bot
from bot.handlers import user
from db.models import User, Task
from moodle import courses, tasks
from moodle.discussions import get_new_discussions
from bot.handlers.user import send_task_to_user, send_tasks_to_user
from config import bot_loger
from moodle.tasks import get_new_tasks
from db.base import init_db


class UserTasks(NamedTuple):
    user_id: int
    tasks: list[Task]


async def get_user_tasks(moodle_token: str, user_id: int):
    get_time = time.time()
    async with aiohttp.ClientSession() as session:
        user_courses = await courses.get_user_courses(moodle_token, session)

    "Получение заданий для каждого курса"
    async_tasks = []
    for course in user_courses:
        async_tasks.append(get_new_tasks(moodle_token, course))
        async_tasks.append(get_new_discussions(moodle_token, course))

    all_course_tasks = await asyncio.gather(*async_tasks)
    all_course_tasks = [task for course_tasks in all_course_tasks for task in course_tasks]

    "Отправка уведомлений"
    await send_tasks_to_user(user_id, all_course_tasks)
    return all_course_tasks


async def main():
    start = time.time()

    all_users = await User.get_all()
    all_users = all_users * 1
    # print(f'All users: {len(all_users)}')

    "Получение заданий для всех пользователей и отправка уведомлений"
    async_tasks = []
    for user in all_users:
        async_tasks.append(get_user_tasks(user.moodle_token, user.id))

    all_tasks = await asyncio.gather(*async_tasks)
    all_tasks = [task for user_tasks in all_tasks for task in user_tasks]

    print(f'Time: {time.time() - start}')
    # print(all_tasks)


async def on_startup(dispatcher):
    # await init_db()
    await user.register_handlers(dispatcher)
    await main()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)

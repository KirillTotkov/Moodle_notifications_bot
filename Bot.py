import asyncio
import time
from pprint import pprint

from aiogram import executor

from bot.create_bot import dp
from bot.handlers import user
from db.models import User
from moodle import courses, tasks
from moodle.discussions import get_new_discussions
from bot.handlers.user import send_tasks_to_user


async def get_user_tasks(moodle_token: str):
    user_courses = await courses.get_user_courses(moodle_token)
    async_tasks = []
    for course in user_courses:
        async_tasks.append(tasks.get_new_tasks(moodle_token, course))
        async_tasks.append(get_new_discussions(moodle_token, course))

    user_tasks = await asyncio.gather(*async_tasks)

    return user_tasks


async def main():
    start = time.time()

    all_users = await User.get_all()
    all_users = all_users * 5
    print(f'All users: {len(all_users)}')

    "Получение заданий для всех пользователей и отправка уведомлений"
    async_tasks = []
    for user in all_users:
        async_tasks.append(get_user_tasks(user.moodle_token))

    all_user_tasks = await asyncio.gather(*async_tasks)
    print(f'All user tasks: {len(all_users) * 10}')

    for user, user_tasks in zip(all_users, all_user_tasks):
        for user_task in user_tasks:
            if user_task:
                await send_tasks_to_user(user, user_task)

    # async_tasks = []
    # for user, user_tasks in zip(all_users, all_user_tasks):
    #     for user_task in user_tasks:
    #         if user_task:
    #             async_tasks.append(send_tasks_to_user(user, user_task))
    #
    # await asyncio.gather(*async_tasks)

    print(f'Time: {time.time() - start}')


async def on_startup(dispatcher):
    await user.register_handlers(dispatcher)
    await main()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)

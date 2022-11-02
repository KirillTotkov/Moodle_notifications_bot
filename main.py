import asyncio
import time

from aiohttp import ClientSession
from sqlalchemy import select

from moodle import courses, tasks
from db.base import init_db, async_session
from db.models import *
from config import moodle_loger
from moodle.courses import get_user_courses
from moodle.discussions import get_new_discussions, get_new_discussions_from_courses
from moodle.tasks import get_new_tasks


async def run(moodle_token: str):
    time_start = time.time()
    # user_courses = [Course(id=9, name='Bioorganic Chemistry'), Course(id=8, name='Analog Electronics'),
    #                 Course(id=4, name='Физика'), Course(id=3, name='Сети'), Course(id=2, name='Математика')]

    user_courses = await courses.get_user_courses(moodle_token)

    async_tasks = []
    for course in user_courses:
        async_tasks.append(tasks.get_new_tasks(moodle_token, course))
        async_tasks.append(get_new_discussions(moodle_token, course))

    user_tasks = await asyncio.gather(*async_tasks)

    return user_tasks


async def main():
    from config import token
    start = time.time()
    new_user = await User.get_or_create(username='test', first_name='test', moodle_token=token)

    all_users = await User.get_all()
    all_users = all_users*300
    async_tasks = []
    for user in all_users:
        async_tasks.append(run(user.moodle_token))

    user_tasks = await asyncio.gather(*async_tasks)
    print(user_tasks)

    print(f'Time: {time.time() - start}')


if __name__ == '__main__':
    asyncio.run(main())

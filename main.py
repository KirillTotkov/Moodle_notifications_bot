import asyncio
import time

from sqlalchemy import select

from moodle import courses, tasks
from db.base import init_db, async_session
from db.models import *
from db.query import get, get_all
from config import moodle_loger
from moodle.discussions import get_new_discussions


async def run(token):
    time_start = time.time()
    # user_courses = [Course(id=9, name='Bioorganic Chemistry'), Course(id=8, name='Analog Electronics'),
    #                 Course(id=4, name='Физика'), Course(id=3, name='Сети'), Course(id=2, name='Математика')]

    user_courses = await courses.get_user_courses(token)

    async_tasks = []
    for course in user_courses:
        async_tasks.append(tasks.get_new_tasks(token, course))
        async_tasks.append(get_new_discussions(token, course))

    user_tasks = await asyncio.gather(*async_tasks)

    return user_tasks


async def main():
    from config import token

    start = time.time()

    tokens = [token] * 100
    # for token in tokens:
    #     await run(token)
    async_tasks = []
    for token in tokens:
        async_tasks.append(run(token))

    await asyncio.gather(*async_tasks)

    print(f'Time: {time.time() - start}')


if __name__ == '__main__':
    asyncio.run(main())

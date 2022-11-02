import time
from json import JSONDecodeError
from pprint import pprint
import asyncio

import aiohttp
from aiohttp import ClientSession

from config import MOODLE_HOST, ADMIN_MOODLE_TOKEN
from moodle.courses import Course
from db.models import Task


async def get_new_tasks_from_courses(moodle_token: str, courses: list) -> list:
    """Get new tasks from courses"""
    async_tasks = []
    for course in courses:
        async_tasks.append(get_new_tasks(moodle_token, course))
    tasks = await asyncio.gather(*async_tasks)
    return tasks


async def get_new_tasks(moodle_token: str, course: Course) -> list:
    """Get new tasks from Moodle"""
    tasks_from_moodle = await get_course_tasks(moodle_token, course.id)
    tasks_from_db = []
    new_tasks = set(tasks_from_moodle) ^ set(tasks_from_db)

    # print(
    #     f"Len of new tasks: {len(new_tasks)}, len of tasks from moodle: {len(tasks_from_moodle)}, "
    #     f"len of tasks from db: {len(tasks_from_db)}")

    return list(new_tasks)


async def get_course_tasks(moodle_token: str, course_id: int) -> list:
    """Get all tasks from Moodle"""
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'core_course_get_contents',
        'courseid': course_id,
        'moodlewsrestformat': 'json',
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, ssl=False) as response:
            data = await response.json()
            if 'exception' in data:
                return []
                # raise Exception(data['message'], data.get('debuginfo'), course_id)

            tasks = await parse_tasks(data)
            return tasks


async def parse_tasks(data: dict) -> list:
    tasks = []
    for section in data:
        for module in section['modules']:
            tasks.append(Task(id=module['id'], type=module['modplural'], name=module['name']))
    return tasks[1:]


async def main():
    start = time.time()
    tasks = await get_course_tasks(token, 2)
    end = time.time()
    print(f"Time taken: {end - start}")
    pprint(tasks)


if __name__ == "__main__":
    asyncio.run(main())

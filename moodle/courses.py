import time
from json import JSONDecodeError
from pprint import pprint
import asyncio

import aiohttp
from aiohttp import ClientSession

from config import MOODLE_HOST, ADMIN_MOODLE_TOKEN, moodle_loger
from db.models import Course, User


async def get_new_courses(user: User) -> list:
    """Get new courses from Moodle"""
    async with ClientSession() as session:
        course_from_moodle = await get_user_courses(user.moodle_token, session)
        course_from_db = user.courses
        # print(f'{course_from_db= }')
        new_courses = set(course_from_moodle) ^ set(course_from_db)
        # print(f'{new_courses=}')
        return new_courses


async def get_user_courses(moodle_token: str, session: ClientSession) -> list:
    """Get all courses from Moodle"""
    request_time = time.time()
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'core_course_get_enrolled_courses_by_timeline_classification',
        'classification': 'all',
        'moodlewsrestformat': 'json',
    }
    async with session.get(url, params=params, ssl=False) as response:
        data = await response.json()
        if 'exception' in data:
            raise Exception(data['message'], data.get('debuginfo'))

        courses = [Course(id=course['id'], name=course['fullname']) for course in data['courses']]
        moodle_loger.info(f"Request to Moodle took {time.time() - request_time} seconds")
        return courses


async def main():
    start = time.time()

    courses = await get_user_courses('e37848688ca30f5d49893f42ef159086')
    end = time.time()


if __name__ == "__main__":
    asyncio.run(main())

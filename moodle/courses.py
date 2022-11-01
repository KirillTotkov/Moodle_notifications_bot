import time
from json import JSONDecodeError
from pprint import pprint
import asyncio
from aiohttp import ClientSession

from config import MOODLE_HOST, ADMIN_MOODLE_TOKEN, moodle_loger
from db.models import Course



async def get_user_courses(moodle_token: str) -> list:
    """Get all courses from Moodle"""
    request_time = time.time()
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'core_course_get_enrolled_courses_by_timeline_classification',
        'classification': 'all',
        'moodlewsrestformat': 'json',
    }
    async with ClientSession() as session:
        async with session.get(url, params=params, ssl=False) as response:
            data = await response.json()
            courses = [Course(id=course['id'], name=course['fullname']) for course in data['courses']]


async def main():
    start = time.time()

    courses = await get_user_courses('e37848688ca30f5d49893f42ef159086')
    end = time.time()


if __name__ == "__main__":
    asyncio.run(main())

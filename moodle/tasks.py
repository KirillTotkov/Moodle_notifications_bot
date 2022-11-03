from io import BytesIO
import asyncio
from aiohttp import ClientSession

from config import MOODLE_HOST
from moodle.courses import Course
from db.models import Task


async def _get_file(url: str) -> BytesIO:
    async with ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            file_name = response.headers['Content-Disposition'].split('=')[1].replace('"', '') \
                .encode('latin-1').decode('utf-8')
            file = BytesIO(data)
            file.name = file_name
            return file


async def get_new_tasks(moodle_token: str, course: Course) -> list:
    """Get new tasks from Moodle"""
    tasks_from_moodle = await get_course_tasks(moodle_token, course)
    tasks_from_db = await course.get_tasks()
    new_tasks = set(tasks_from_moodle) ^ set(tasks_from_db)
    return list(new_tasks)


async def get_course_tasks(moodle_token: str, course: Course) -> list:
    """Get all tasks from Moodle"""
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'core_course_get_contents',
        'courseid': course.id,
        'moodlewsrestformat': 'json',
    }
    async with ClientSession() as session:
        async with session.get(url, params=params, ssl=False) as response:
            data = await response.json()
            if 'exception' in data:
                return []

            tasks = await parse_tasks(data, course)
            return tasks


async def parse_tasks(data: dict, course) -> list[Task]:
    tasks = []
    for section in data:
        for module in section['modules']:
            tasks.append(
                Task(
                    id=module['id'],
                    type=module['modplural'],
                    name=module['name'],
                    description=module.get('description'),
                    url=module.get('url'),
                    course_id=course.id,
                    course=course,
                )
            )
    return tasks[1:]
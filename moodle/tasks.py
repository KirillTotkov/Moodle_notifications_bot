from io import BytesIO
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from config import MOODLE_HOST, headers
from moodle.courses import Course, TokenException
from db.models import Task


async def get_file(url: str) -> BytesIO:
    async with ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            file_name = response.headers['Content-Disposition'].split('filename=')[1]
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
        async with session.get(url, params=params, headers=headers) as response:
            data = await response.json()
            if 'exception' in data:
                if data['errorcode'] == 'invalidtoken':
                    raise TokenException(data['message'])
                raise Exception(data['message'], data.get('debuginfo'))

            tasks = _parse_tasks(data, course)
            return tasks


def _parse_tasks(data: dict, course: Course) -> list[Task]:
    tasks = []
    for section in data:
        for module in section['modules']:
            tasks.append(
                Task(
                    id=module['id'],
                    type=module['modplural'],
                    name=module['name'],
                    description=_parse_task_description(module),
                    hyperlink=_parse_task_hyperlink(module),
                    url=module.get('url'),
                    course=course,
                )
            )
    return tasks


def _parse_task_hyperlink(task: dict) -> str:
    if "contents" in task and task["contents"]:
        return task['contents'][0]['fileurl'].replace('forcedownload=1', '')


def _parse_task_description(task: dict) -> str:
    if "description" in task:
        soup = BeautifulSoup(task['description'], 'html.parser')
        return soup.get_text(separator='\n')

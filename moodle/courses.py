from aiohttp import ClientSession

from config import MOODLE_HOST, headers
from db.models import Course, User


async def set_courses_forum_id(moodle_token: str, courses: set[Course]) -> list[Course]:
    for course in courses:
        course.forum_id = await get_forum_id_by_course(moodle_token, course.id)
    return list(courses)


async def get_forum_id_by_course(moodle_token: str, course_id: int) -> int:
    """Get forum id by course id"""
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'mod_forum_get_forums_by_courses',
        'courseids[0]': course_id,
        'moodlewsrestformat': 'json',
    }
    async with ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            data = await response.json()
            if 'exception' in data:
                raise Exception(data['message'], data.get('debuginfo'), course_id)
            return data[0]['id']


async def get_new_courses(user: User) -> list[Course]:
    """Get new courses from Moodle"""
    course_from_moodle = await get_courses_from_moodle(user.moodle_token)
    course_from_db = user.courses
    new_courses = set(course_from_moodle) ^ set(course_from_db)

    "Для новых курсов сохраняем форума"
    if new_courses:
        new_courses = await set_courses_forum_id(user.moodle_token, new_courses)
        return new_courses
    return []


async def get_courses_from_moodle(moodle_token) -> list[Course]:
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'core_course_get_enrolled_courses_by_timeline_classification',
        'classification': 'all',
        'moodlewsrestformat': 'json',
    }
    async with ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            if 'exception' in data:
                raise Exception(data['message'], data.get('debuginfo'))
            courses = [
                Course(
                    id=course['id'],
                    name=course['fullname'].split(', гр.')[0],
                ) for course in data['courses']
            ]

            return courses

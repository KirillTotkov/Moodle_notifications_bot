from aiohttp import ClientSession

from config import MOODLE_HOST, headers
from db.models import Course, User
from moodle.discussions import get_forum_id_by_course


async def get_new_courses(user: User) -> list[Course]:
    """Get new courses from Moodle"""
    async with ClientSession() as session:
        course_from_moodle = await get_user_courses(user.moodle_token, session)
        course_from_db = await user.get_courses()
        new_courses = set(course_from_moodle) ^ set(course_from_db)
        return list(new_courses)


async def get_user_courses(moodle_token: str, session: ClientSession) -> list[Course]:
    """Get all courses from Moodle"""
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'core_course_get_enrolled_courses_by_timeline_classification',
        'classification': 'all',
        'moodlewsrestformat': 'json',
    }
    async with session.get(url, params=params, headers=headers) as response:
        data = await response.json()
        if 'exception' in data:
            raise Exception(data['message'], data.get('debuginfo'))

        courses = [
            Course(
                id=course['id'],
                name=course['fullname'].split(', гр.')[0],
                forum_id=await get_forum_id_by_course(moodle_token, course['id']),
            ) for course in data['courses']
        ]

        return courses

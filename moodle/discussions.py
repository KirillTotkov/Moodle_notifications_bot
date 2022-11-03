import aiohttp
from bs4 import BeautifulSoup

from config import MOODLE_HOST
from db.models import Discussion, Course


async def get_new_discussions(moodle_token: str, course: Course) -> list[Discussion]:
    """Get new discussions from Moodle"""
    discussions_from_moodle = await get_discussions(moodle_token, course)
    discussions_from_db = await course.get_discussions()
    new_discussions = set(discussions_from_moodle) ^ set(discussions_from_db)

    return list(new_discussions)


async def get_discussions(moodle_token: str, course: Course) -> list:
    """Get all discussions from Moodle"""
    url = f'{MOODLE_HOST}/webservice/rest/server.php'
    params = {
        'wstoken': moodle_token,
        'wsfunction': 'mod_forum_get_forum_discussions_paginated',
        'forumid': course.id - 1,
        'moodlewsrestformat': 'json',
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, ssl=False) as response:
            data = await response.json()
            if 'exception' in data:
                return []
                # raise Exception(data['message'], data['debuginfo'])
            discussions = await _parse_discussions(data, course)
            return discussions


async def _parse_discussions(data: dict, course: Course) -> list:
    discussions = []
    for discussion in data['discussions']:
        discussions.append(
            Discussion(
                id=discussion['id'],
                name=discussion['name'],
                message=await _parse_message(discussion['message']),
                url=f"{MOODLE_HOST}/mod/forum/discuss.php?d={discussion['id']}",
                course_id=course.id,
                course=course,
            )
        )
    return discussions


async def _parse_message(message: str) -> str:
    soup = BeautifulSoup(message, 'html.parser')
    return soup.get_text('\n')
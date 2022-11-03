import time
from json import JSONDecodeError
from pprint import pprint
import asyncio

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from config import MOODLE_HOST, ADMIN_MOODLE_TOKEN
from db.models import Discussion, Course


async def get_new_discussions(moodle_token: str, course: Course) -> list[Discussion]:
    """Get new discussions from Moodle"""
    discussions_from_moodle = await get_discussions(moodle_token, course)
    discussions_from_db = []
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
            discussions = await parse_discussions(data, course)
            return discussions


async def parse_discussions(data: dict, course: Course) -> list:
    discussions = []
    for discussion in data['discussions']:
        discussions.append(
            Discussion(
                id=discussion['id'],
                name=discussion['name'],
                message=await parse_message(discussion['message']),
                url=f"{MOODLE_HOST}/mod/forum/discuss.php?d={discussion['id']}",
                course_id=course.id,
                course=course,
            )
        )
    return discussions


async def parse_message(message: str) -> str:
    soup = BeautifulSoup(message, 'html.parser')
    return soup.get_text('\n')


async def main():
    token = 'e37848688ca30f5d49893f42ef159086'

    start = time.time()
    discussions = await get_discussions(token, 2)
    end = time.time()
    print(f"Time taken: {end - start}")
    pprint(discussions)


if __name__ == "__main__":
    asyncio.run(main())

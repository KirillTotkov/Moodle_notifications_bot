import asyncio
from pprint import pprint

from db.models import Course
from moodle.discussions import get_forum_id_by_course, get_discussions

token = '1456615c111d61419bd8d958e8a61469'


async def main():
    forum_id = 1
    discussions = await get_discussions(token, Course(id=2, forum_id=forum_id))

    for discussion in discussions:
        print(discussion.id, discussion.name, discussion.url)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import time
from aiohttp import ClientSession

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import RetryAfter

from config import MOODLE_HOST, headers, bot, bot_logger
from db.models import User, Task
from moodle.courses import get_new_courses
from moodle.discussions import get_new_discussions
from moodle.tasks import get_new_tasks, get_file


class UserState(StatesGroup):
    login = State()
    password = State()


async def delete_user_handler(message: types.Message):
    user = await User.get_or_none(id=message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы. Напишите /start")
        return

    await user.remove_courses()
    await user.delete()
    await message.answer("Вы успешно удалили свой аккаунт")


async def get_user_tasks(user: User):
    "Получение заданий для каждого курса"
    async_tasks = []
    for course in user.courses:
        async_tasks.append(get_new_tasks(user.moodle_token, course))
        async_tasks.append(get_new_discussions(user.moodle_token, course))

    all_tasks_discussions = await asyncio.gather(*async_tasks)
    all_tasks_discussions = [task for user_tasks in all_tasks_discussions for task in user_tasks]

    new_courses = await get_new_courses(user)
    if new_courses:
        await user.add_courses(new_courses)

    return all_tasks_discussions, new_courses


async def send_new_tasks_and_courses(user: User):
    tasks, new_courses = await get_user_tasks(user)
    try:
        await send_tasks_to_user(user.id, tasks, user.moodle_token)
    except RetryAfter as e:
        bot_logger.error(f"Retry after {e.timeout}")
        time.sleep(e.timeout * 2)
        await send_tasks_to_user(user.id, tasks, user.moodle_token)

    try:
        await send_tasks_to_user(user.id, new_courses, user.moodle_token)
    except RetryAfter as e:
        bot_logger.error(f"Retry after {e.timeout}")
        time.sleep(e.timeout * 2)
        await send_tasks_to_user(user.id, new_courses, user.moodle_token)

    return tasks


async def send_tasks_to_user(user_id: int, tasks: list, moodle_token: str) -> None:
    send_tasks_time = time.time()

    for task in tasks:
        if isinstance(task, Task) and task.type == "Файлы":
            file = await get_file(f'{task.hyperlink}token={moodle_token}')
            await bot.send_document(user_id, file, caption=str(task), parse_mode="HTML")
        else:
            await bot.send_message(user_id, str(task), parse_mode="HTML")

    bot_logger.info(f'Отправка заданий пользователю {user_id} заняла {time.time() - send_tasks_time} секунд')


def check_user_registered(func):
    async def wrapped(message: types.Message):
        user = await User.get_or_none(id=message.from_user.id)
        if not user:
            await message.answer("Вы не зарегистрированы. Напишите /start")
            return

        await func(message)

    return wrapped


@check_user_registered
async def show_user_courses(message: types.Message) -> None:
    user = await User.get_or_none(id=message.from_user.id)

    courses = user.courses
    if not courses:
        await message.answer('У вас нет курсов')
    else:
        courses_text = ''
        for num, course in enumerate(courses):
            courses_text += f"{num + 1}⃣ {course.name} \n"

        await message.answer(courses_text)


async def get_moodle_token(login: str, password: str) -> str:
    async with ClientSession() as session:
        data = {'username': login, 'password': password, 'service': 'moodle_mobile_app'}
        async with session.post(f'{MOODLE_HOST}/login/token.php', headers=headers, data=data) as response:
            response = await response.json()
            return response.get('token')


async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Canceled")


async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот для уведомлений о новых заданиях в Moodle. ")

    user = await User.get_or_none(id=message.from_user.id)
    if user:
        await message.answer("Вы уже зарегистрированы")
        return

    await message.answer("Для начала работы, введите логин и пароль от Moodle. \n"
                         "Для отмены введите /cancel")
    await message.answer("Логин:")

    await UserState.login.set()


async def login_handler(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Пароль:")
    await UserState.password.set()


async def password_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login = data.get("login")
    password = message.text

    moodle_token = await get_moodle_token(login, password)
    if not moodle_token:
        await message.answer("Неверный логин или пароль! \nПопробуйте еще раз")
        await message.answer("Логин:")
        await UserState.login.set()
        return
    else:
        await message.answer("<b>Вам будут приходить сообщения о новых заданиях</b>", parse_mode="HTML")
        await state.finish()

    user = User(
        id=message.from_user.id,
        username=message.from_user.username,
        moodle_token=moodle_token,
        courses=[]
    )

    bot_logger.info(f'Новый пользователь {user}')

    "добавляем пользователя в БД"
    await user.save()

    "добавляем курсы пользователя в БД"
    user_courses = await get_new_courses(user)
    await user.add_courses(user_courses)

    "добавляем задания и обсуждения в БД"
    tasks, _ = await get_user_tasks(user)
    for task in tasks:
        await task.save()

    await message.answer("Ваши курсы:")
    await show_user_courses(message)

    bot_logger.info(f'Новый пользователь {user}')


async def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands=["start"], state="*")
    dp.register_message_handler(cancel_handler, commands=["cancel"], state="*")
    dp.register_message_handler(login_handler, state=UserState.login)
    dp.register_message_handler(password_handler, state=UserState.password)
    dp.register_message_handler(show_user_courses, commands=["show_courses"])
    dp.register_message_handler(delete_user_handler, commands=["delete_me"])

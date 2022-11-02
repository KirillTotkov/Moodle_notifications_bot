import asyncio
import time

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import RetryAfter
from aiohttp import ClientSession

from bot.create_bot import bot
from config import MOODLE_HOST, bot_loger
from db.models import User, Task


class UserState(StatesGroup):
    login = State()
    password = State()


async def send_tasks_to_user(user: User, tasks: list[Task]):
    send_tasks_time = time.time()
    # async_task = []
    # for task in tasks:
    #     async_task.append(bot.send_message(user.id, task.name))
    #
    # await asyncio.gather(*async_task)

    for task in tasks:
        try:
            await bot.send_message(user.id, task.name)
            await asyncio.sleep(0.1)
        except RetryAfter:
            print("RetryAfter")
            await asyncio.sleep(10)
            await bot.send_message(user.id, task.name)

    bot_loger.info(f"Send tasks to user {user.id} time: {time.time() - send_tasks_time}")


def check_user_registered(func):
    async def wrapped(message: types.Message):
        user = await User.get_or_none(id=message.from_user.id)
        if not user:
            await message.answer("Вы не зарегистрированы. Напишите /start")
            return

        await func(message)

    return wrapped


@check_user_registered
async def show_user_courses(message: types.Message):
    user = await User.get_or_none(id=message.from_user.id)

    courses = await user.get_courses()
    if not courses:
        await message.answer('У вас нет курсов')
        return

    for num, course in enumerate(courses):
        await message.answer(f'{num + 1}⃣ {course.name}\n')


async def get_moodle_token(login: str, password: str) -> str:
    async with ClientSession() as session:
        async with session.post(f"{MOODLE_HOST}/login/token.php", data={
            "username": login,
            "password": password,
            "service": "moodle_mobile_app"
        }) as response:
            data = await response.json()
            return data.get("token")


async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Canceled")


async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот для уведомлений о новых заданиях в Moodle. ")

    user = await User.get_or_none(id=message.from_user.id)
    if user:
        await message.answer("Вы уже зарегистрированы. Напишите /show_my_courses")
        return

    await message.answer("Для начала работы, введите логин и пароль от Moodle")
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
        await message.answer('Неверный логин или пароль, попробуйте заново.')
        await UserState.login.set()
        return

    user = User(
        id=message.from_user.id,
        username=message['from']['username'],
        first_name=message['from']['first_name'],
        moodle_token=moodle_token,
    )

    "добавляем пользователя в БД"
    await user.create()

    await message.answer("Вам будут приходить сообщения о новых заданиях")

    await state.finish()


async def register_handlers(dp):
    dp.register_message_handler(start_handler, commands=["start"], state="*")
    dp.register_message_handler(cancel_handler, commands=["cancel"], state="*")
    dp.register_message_handler(login_handler, state=UserState.login)
    dp.register_message_handler(password_handler, state=UserState.password)
    dp.register_message_handler(show_user_courses, commands=["show_my_courses"])

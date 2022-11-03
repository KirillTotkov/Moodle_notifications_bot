import asyncio
import time
from aiohttp import ClientSession

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import RetryAfter


from bot.create_bot import bot
from config import MOODLE_HOST, bot_loger
from db.models import User
from moodle.courses import get_new_courses


class UserState(StatesGroup):
    login = State()
    password = State()


async def send_tasks_to_user(user_id: int, tasks: list):
    send_tasks_time = time.time()

    for task in tasks:
        try:
            await bot.send_message(user_id, str(task), parse_mode='HTML')
        except RetryAfter as e:
            print(e)
            bot_loger.error(f"Retry after {e.timeout}")
            await asyncio.sleep(e.timeout * 2)
            await bot.send_message(user_id, task.name)

    bot_loger.info(f"Send tasks to user {user_id} time: {time.time() - send_tasks_time}")


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

    courses_text = ''
    for num, course in enumerate(courses):
        courses_text += f"{num + 1}⃣  {course.name} \n"

    await message.answer(courses_text)


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
        courses=[]
    )

    "добавляем пользователя в БД"
    await user.save()
    "добавляем курсы пользователя в БД"
    user_courses = await get_new_courses(user)
    await user.add_courses(user_courses)

    await message.answer("Вам будут приходить сообщения о новых заданиях")

    await state.finish()


async def register_handlers(dp):
    dp.register_message_handler(start_handler, commands=["start"], state="*")
    dp.register_message_handler(cancel_handler, commands=["cancel"], state="*")
    dp.register_message_handler(login_handler, state=UserState.login)
    dp.register_message_handler(password_handler, state=UserState.password)
    dp.register_message_handler(show_user_courses, commands=["show_courses"])

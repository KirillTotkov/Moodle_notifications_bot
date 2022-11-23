from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, InlineKeyboardButton

from bot.create_bot import scheduler
from config import BOT_ADMIN_ID
from db.models import User


class Admin(StatesGroup):
    job_time = State()


class Keyboard:
    admin = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    admin.add(KeyboardButton('Посмотреть задачу'))
    admin.add(KeyboardButton('Назад'))


class InlineKeyboard:
    admin = InlineKeyboardMarkup(row_width=2)
    admin.add(InlineKeyboardButton('Изменить период', callback_data='change_time'))
    admin.add(InlineKeyboardButton('Запустить задачу', callback_data='run_job'))
    admin.add(InlineKeyboardButton('Приостановить задачу', callback_data='pause_job'))


def check_admin(func):
    async def wrapper(message: types.Message):
        if message.from_user.id != BOT_ADMIN_ID:
            return None
        return await func(message)

    return wrapper


@check_admin
async def get_users(message: types.Message):
    "Отправляет список пользователей. Если их больше 10, то отправляет по 10 пользователей"
    users = await User.get_all()
    await message.answer(f'Пользователей в базе: {len(users)}')
    for i in range(0, len(users), 10):
        await message.answer('\n'.join([f'@{user.username}' for user in users[i:i + 10]]))


@check_admin
async def admin(message: types.Message):
    await message.answer('Вы вошли в админ панель', reply_markup=Keyboard.admin)


@check_admin
async def show_job(message: types.Message):
    job = scheduler.get_jobs()[0]
    message_text = f'<b>ID задачи</b>: <i>{job.id}</i>\n' \
                   f'<b>Период</b>: <i>{job.trigger}</i>\n' \
                   f'<b>Время следующего запуска</b>: ' \
                   f'<i>{job.next_run_time.strftime("%H:%M:%S") if job.next_run_time else "остановлена"}</i>\n' \
                   f'Функция: <i>{job.func_ref}</i>'
    await message.answer(message_text, reply_markup=InlineKeyboard.admin, parse_mode='HTML')


@check_admin
async def change_time(call: types.CallbackQuery):
    await call.message.answer('Введите новое время в секундах')
    await call.answer()
    await Admin.job_time.set()


async def change_time_set(message: types.Message, state: FSMContext):
    job = scheduler.get_jobs()[0]
    try:
        job_time = int(message.text)
        job.reschedule(trigger='interval', seconds=job_time)
        await message.answer('Период изменен', reply_markup=Keyboard.admin)
        await state.finish()
    except ValueError:
        await message.answer('Неверный формат')


async def run_job(call: types.CallbackQuery):
    job = scheduler.get_jobs()[0]
    job.resume()
    await call.message.answer('Задача запущена')
    await call.answer()


@check_admin
async def pause_job(call: types.CallbackQuery):
    job = scheduler.get_jobs()[0]
    job.pause()
    await call.message.answer('Задача приостановлена')
    await call.answer()


@check_admin
async def back(message: types.Message):
    await message.answer('Вы вышли из админ панели', reply_markup=ReplyKeyboardRemove())


async def register_handlers(dp: Dispatcher):
    dp.register_message_handler(admin, commands='admin', state='*')
    dp.register_message_handler(show_job, text='Посмотреть задачу', state='*')
    dp.register_callback_query_handler(change_time, text='change_time', state='*')
    dp.register_message_handler(change_time_set, state=Admin.job_time)
    dp.register_callback_query_handler(run_job, text='run_job', state='*')
    dp.register_callback_query_handler(pause_job, text='pause_job', state='*')
    dp.register_message_handler(back, text='Назад', state='*')
    dp.register_message_handler(get_users, commands='users', state='*')

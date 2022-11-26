from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import IDFilter

from config import BOT_ADMIN_ID, scheduler
from db.models import User, Course


class Admin(StatesGroup):
    job_time = State()
    delete_last_task = State()


class Keyboard:
    admin = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    admin.add(KeyboardButton('Посмотреть задачу'))
    admin.add(KeyboardButton('Посмотреть пользователей'))
    admin.add(KeyboardButton('Удалить последнее задание'))
    admin.add(KeyboardButton('Назад'))


class InlineKeyboard:
    admin = InlineKeyboardMarkup(row_width=2)
    admin.add(InlineKeyboardButton('Изменить период', callback_data='change_time'))
    admin.add(InlineKeyboardButton('Запустить задачу', callback_data='run_job'))
    admin.add(InlineKeyboardButton('Приостановить задачу', callback_data='pause_job'))


async def delete_last_task(message: types.Message):
    """
    Для тестирования отправки сообщений.
    Удалить последнее задание курса
    """
    courses = await Course.get_all()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('Назад в админ панель'))
    for course in courses:
        markup.add(KeyboardButton(course.name))
    await message.answer('Выберите курс', reply_markup=markup)
    await Admin.delete_last_task.set()


async def bask_to_admin_panel(message: types.Message, state: FSMContext):
    await message.answer('Вы вошли в админ панель', reply_markup=Keyboard.admin)
    await state.finish()


async def delete_last_task_set(message: types.Message, state: FSMContext):
    course = await Course.get_or_none(name=message.text)
    await course.delete_last_task()
    await message.answer(f'Последнее задание курса <b>{course.name}</b> удалено', reply_markup=Keyboard.admin,
                         parse_mode='HTML')
    await state.finish()


async def get_users(message: types.Message):
    "Отправляет список пользователей. Если их больше 10, то отправляет по 10 пользователей"
    users = await User.get_all()
    await message.answer(f'Пользователей в базе: {len(users)}')
    for i in range(0, len(users), 10):
        await message.answer('\n'.join([f'@{user.username}' for user in users[i:i + 10]]))


async def admin(message: types.Message):
    await message.answer('Вы вошли в админ панель', reply_markup=Keyboard.admin)


async def show_job(message: types.Message):
    job = scheduler.get_jobs()[0]
    message_text = f'<b>ID задачи</b>: <i>{job.id}</i>\n' \
                   f'<b>Период</b>: <i>{job.trigger}</i>\n' \
                   f'<b>Время следующего запуска</b>: ' \
                   f'<i>{job.next_run_time.strftime("%H:%M:%S") if job.next_run_time else "остановлена"}</i>\n' \
                   f'Функция: <i>{job.func_ref}</i>'
    await message.answer(message_text, reply_markup=InlineKeyboard.admin, parse_mode='HTML')


async def change_time(call: types.CallbackQuery):
    await call.message.answer('Введите новое время в секундах')
    await call.answer()
    await Admin.job_time.set()


async def change_time_set(message: types.Message, state: FSMContext):
    job = scheduler.get_jobs()[0]
    job_time = message.text
    if not job_time.isdigit() or int(job_time) < 1:
        await message.answer('Неверный формат времени')
        await state.finish()
        return

    job.reschedule(trigger='interval', seconds=int(job_time))
    await message.answer('Период изменен', reply_markup=Keyboard.admin)
    await state.finish()


async def run_job(call: types.CallbackQuery):
    job = scheduler.get_jobs()[0]
    job.resume()
    await call.message.answer('Задача запущена')
    await call.answer()


async def pause_job(call: types.CallbackQuery):
    job = scheduler.get_jobs()[0]
    job.pause()
    await call.message.answer('Задача приостановлена')
    await call.answer()


async def back(message: types.Message, state: FSMContext):
    await message.answer('Вы вышли из админ панели', reply_markup=ReplyKeyboardRemove())
    await state.finish()


async def register_handlers(dp: Dispatcher):
    dp.register_message_handler(admin, IDFilter(user_id=BOT_ADMIN_ID), commands='admin')
    dp.register_message_handler(show_job, IDFilter(user_id=BOT_ADMIN_ID), text='Посмотреть задачу')
    dp.register_callback_query_handler(change_time, IDFilter(user_id=BOT_ADMIN_ID), text='change_time', state='*')
    dp.register_message_handler(change_time_set, IDFilter(user_id=BOT_ADMIN_ID), state=Admin.job_time)
    dp.register_callback_query_handler(run_job, IDFilter(user_id=BOT_ADMIN_ID), text='run_job', state='*')
    dp.register_callback_query_handler(pause_job, IDFilter(user_id=BOT_ADMIN_ID), text='pause_job', state='*')
    dp.register_message_handler(back, IDFilter(user_id=BOT_ADMIN_ID), text='Назад', state='*')
    dp.register_message_handler(get_users, IDFilter(user_id=BOT_ADMIN_ID), text='Посмотреть пользователей')
    dp.register_message_handler(delete_last_task, IDFilter(user_id=BOT_ADMIN_ID), text='Удалить последнее задание')
    dp.register_message_handler(bask_to_admin_panel, IDFilter(user_id=BOT_ADMIN_ID), text='Назад в админ панель',
                                state='*')
    dp.register_message_handler(delete_last_task_set, IDFilter(user_id=BOT_ADMIN_ID), state=Admin.delete_last_task)


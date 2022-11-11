from sqlite3 import IntegrityError

from sqlalchemy import Column, Integer, String, ForeignKey, Table, PrimaryKeyConstraint, TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.future import select

from db.base import Base, async_session
from config import db_loger

Users_Courses = Table(
    'users_courses',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('course_id', Integer, ForeignKey('course.id')),
    PrimaryKeyConstraint('user_id', 'course_id')
)


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

    @classmethod
    async def get_or_none(cls, **kwargs):
        async with async_session() as session:
            query = select(cls).filter_by(**kwargs)
            result = await session.execute(query)
            return result.scalars().first()

    @classmethod
    async def get_all(cls):
        async with async_session() as session:
            query = select(cls)
            result = await session.execute(query)
            return result.scalars().all()

    async def save(self):
        async with async_session() as session:
            session.add(self)
            try:
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                db_loger.error(e)
                print(e)

    async def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        await self.save()

    async def delete(self):
        await self.update(deleted=True)


class Course(BaseModel):
    __tablename__ = 'course'

    name = Column(String, nullable=False)
    forum_id = Column(Integer, nullable=True)

    tasks = relationship('Task', back_populates='course')
    discussions = relationship('Discussion', back_populates='course')

    async def get_tasks(self):
        async with async_session() as session:
            query = select(Task).filter_by(course_id=self.id)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_discussions(self):
        async with async_session() as session:
            query = select(Discussion).filter_by(course_id=self.id)
            result = await session.execute(query)
            return result.scalars().all()

    def __str__(self):
        return f'Новый курс: <b>{self.name}</b>'

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'


class User(BaseModel):
    __tablename__ = 'user'

    username = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    moodle_token = Column(String, nullable=False)

    courses = relationship('Course', secondary=Users_Courses, backref='users', lazy='subquery')

    async def add_courses(self, courses):
        for course in courses:
            "Проверить существует ли курс"
            if not await Course.get_or_none(id=course.id):
                await course.save()

            """Если курс не привязан к пользователю, то привязываем"""
            if course not in self.courses:
                db_course = await course.get_or_none(id=course.id)
                self.courses.append(db_course)
        await self.save()

    async def remove_course(self, course):
        if course in self.courses:
            self.courses.remove(course)
            return True
        return False

    async def get_courses(self):
        async with async_session() as session:
            query = select(Course).join(Users_Courses, Users_Courses.c.course_id == Course.id).filter(
                Users_Courses.c.user_id == self.id)
            result = await session.execute(query)
            return result.scalars().all()

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} username={self.username}>'


class Task(BaseModel):
    __tablename__ = 'task'

    name = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    type = Column(String, nullable=False)
    url = Column(String, nullable=True)
    description = Column(TEXT, nullable=True)
    hyperlink = Column(String, nullable=True)

    course = relationship('Course', back_populates='tasks')

    def __str__(self):
        text = f'<b>Курс</b>: {self.course.name}\n' \
               f'<b>Тип</b>: {self.type}\n' \
               f'<b>Название</b>: {self.name}\n'

        if self.type != 'Пояснения':
            text += f'<b>Ссылка</b>: {self.url}\n'

        if self.description:
            text += f'<b>Описание</b>:\n {self.description}\n'

        if self.type == 'Файлы':
            return text

        if self.hyperlink and self.type != 'Папки' and self.type != 'Страницы':
            text += f'<b>Гиперссылка</b>: {self.hyperlink}\n'

        return text

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} type={self.type} name={self.name}>'


class Discussion(BaseModel):
    __tablename__ = 'discussion'

    name = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    url = Column(String, nullable=False)
    message = Column(String, nullable=False)

    course = relationship('Course', back_populates='discussions')

    def __str__(self):
        return f'Новое обсуждение в курсе <b>{self.course.name}</b>:\n' \
               f"<a href='{self.url}'>{self.name}</a>\n\n" \
               f"{self.message}"

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

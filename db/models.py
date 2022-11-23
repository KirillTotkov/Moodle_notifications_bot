from sqlite3 import IntegrityError

from sqlalchemy import Column, Integer, String, ForeignKey, Table, PrimaryKeyConstraint, Text
from sqlalchemy.orm import relationship
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import BIGINT

from config import db_loger
from db.session import Base, async_session

Users_Courses = Table(
    'users_courses',
    Base.metadata,
    Column('user_id', BIGINT, ForeignKey('users.id', ondelete='CASCADE')),
    Column('course_id', BIGINT, ForeignKey('courses.id', ondelete='CASCADE')),
    PrimaryKeyConstraint('user_id', 'course_id')
)


class BaseModel(Base):
    __abstract__ = True

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
        async with async_session() as session:
            await session.delete(self)
            await session.commit()


class Course(BaseModel):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    forum_id = Column(Integer, nullable=True)

    tasks = relationship('Task', back_populates='course', lazy='selectin', cascade='all, delete')
    discussions = relationship('Discussion', back_populates='course', lazy='selectin', cascade='all, delete')

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
    __tablename__ = 'users'

    id = Column(BIGINT, primary_key=True, index=True)
    username = Column(String, nullable=False)
    moodle_token = Column(String, nullable=False)

    courses = relationship('Course', secondary=Users_Courses, backref='users', lazy='selectin',
                           cascade='all, delete')

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

    async def remove_courses(self):
        """Удаляем все курсы пользователя"""
        self.courses = []
        await self.save()

        """Удаляем все курсы, которые не привязаны ни к одному пользователю"""
        async with async_session() as session:
            query = select(Course).filter(~Course.users.any())
            result = await session.execute(query)
            courses = result.scalars().all()
            for course in courses:
                await session.delete(course)
            await session.commit()

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id}, username=@{self.username}>'


class Task(BaseModel):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    url = Column(String)
    description = Column(Text, nullable=True)
    hyperlink = Column(String, nullable=True)

    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="tasks")

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
    __tablename__ = 'discussions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    url = Column(String, nullable=False)

    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    course = relationship('Course', back_populates='discussions')

    def __str__(self):
        return f'Новое обсуждение в курсе <b>{self.course.name}</b>:\n' \
               f"<a href='{self.url}'>{self.name}</a>\n\n" \
               f"{self.text}"

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

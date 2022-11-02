from sqlalchemy import Column, Integer, String, ForeignKey, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.future import select

from db.base import Base, async_session


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

    def __str__(self):
        return self.__repr__()

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
    async def get_or_create(cls, **kwargs):
        obj = await cls.get_or_none(**kwargs)
        if obj:
            return obj, False
        obj = cls(**kwargs)
        await obj.create()
        return obj, True

    @classmethod
    async def get(cls, **kwargs):
        async with async_session() as session:
            obj = await session.get(cls, **kwargs)
            if not obj:
                raise ValueError(f'{cls.__name__} not found')
            return obj

    @classmethod
    async def get_all(cls):
        async with async_session() as session:
            query = select(cls)
            result = await session.execute(query)
            return result.scalars().all()

    async def create(self):
        async with async_session() as session:
            session.add(self)
            await session.commit()

    async def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        await self.save()

    async def delete(self):
        await self.update(deleted=True)


class User(BaseModel):
    __tablename__ = 'user'

    username = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    moodle_token = Column(String(255), nullable=False)

    courses = relationship('Course', secondary=Users_Courses, back_populates='users')

    def add_course(self, course):
        if course not in self.courses:
            self.courses.append(course)
            return True
        return False

    async def remove_course(self, course):
        if course in self.courses:
            self.courses.remove(course)
            return True
        return False

    async def get_courses(self):
        return self.courses

    async def send_message(self, text):
        return self.bot.send_message(self.id, text)

    # async def add_course(self, course):
    #     if course not in self.courses:
    #         self.courses.append(course)
    #         await self.update(courses=self.courses).apply()
    #
    # async def remove_course(self, course):
    #     if course in self.courses:
    #         self.courses.remove(course)
    #         await self.update(courses=self.courses).apply()

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} username={self.username}>'


class Course(BaseModel):
    __tablename__ = 'course'

    name = Column(String(255), nullable=False)

    users = relationship('User', secondary=Users_Courses, back_populates='courses')

    tasks = relationship('Task', back_populates='course')
    discussions = relationship('Discussion', back_populates='course')

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'


class Task(BaseModel):
    __tablename__ = 'task'

    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    type = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)

    course = relationship('Course', back_populates='tasks')

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} type={self.type} name={self.name}>'


class Discussion(BaseModel):
    __tablename__ = 'discussion'

    name = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    url = Column(String(255), nullable=False)
    message = Column(String(255), nullable=False)

    course = relationship('Course', back_populates='discussions')

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

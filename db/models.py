from sqlalchemy import Column, Integer, String, ForeignKey, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from db.base import Base

Users_Courses = Table(
    'users_courses',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('course_id', Integer, ForeignKey('course.id')),
    PrimaryKeyConstraint('user_id', 'course_id')
)


class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    tasks = relationship('Task', backref='course')
    discussions = relationship('Discussion', backref='course')

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

    def __repr__(self):
        return f"Course(id={self.id!r}, name={self.name!r})"


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    type = Column(String, nullable=False)
    url = Column(String, nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

    def __repr__(self):
        return f"Task(id={self.id!r}, type={self.type!r}, name={self.name!r})"


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    fist_name = Column(String, nullable=False)

    moodle_token = Column(String, nullable=False)

    courses = relationship(
        'Course', secondary=Users_Courses, backref='users',
    )

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

    def __repr__(self):
        return f"User(id={self.id}, username={self.username})"


class Discussion(Base):
    __tablename__ = 'discussion'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    message = Column(String, nullable=False)
    url = Column(String, nullable=False)

    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    # course = relationship('Course', backref='discussions')

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id

    def __repr__(self):
        return f"Discussion(id={self.id}, text={self.name})"

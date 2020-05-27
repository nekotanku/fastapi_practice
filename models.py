#sqlalchemy

from datetime import datetime

from db import Base

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.dialects.mysql import INTEGER, BOOLEAN

import hashlib

SQLITE3_NAME = "./db.sqlite3"

class User(Base):
    __tablename__ = 'user'
    id = Column(
        'id',
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True
    )
    username = Column('username', String(256))
    password = Column('password', String(256))
    mail = Column('mail', String(256))

    def __init__(self, username, password, mail):
        self.username = username
        self.password = hashlib.md5(password.encode()).hexdigest()
        self.mail = mail

    def __str__(self):
        return str(self.id) + ':' + self.username

class Task(Base):
    __tablename__ = 'task'
    id = Column(
        'id',
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )
    user_id = Column('user_id', ForeignKey('user_id'))
    content = Column('content', String(256))
    deadline = Column(
        'deadline',
        DateTime,
        default=None,
        nullable=False,
    )
    date = Column(
        'date',
        DateTime,
        default=datetime.now(),
        nullable=False,
        server_default=current_timestamp(),
    )
    done = Column('done', BOOLEAN, default=False, nullable=False)

    def __init__(self, user_id: int, content: str, deadline: datetime, date: datetime = datetime.now()):
        self.user_id = user_id
        self.content = content
        self.deadline = deadline
        self.date = date
        self.done = False
    #デバッグ用
    def __str__(self):
        return str(self.id) + \
            ':user_id ->' + str(self.user_id) + \
            ', content ->' + self.content + \
            ',deadline ->' + self.deadline.strftime('%Y/%m/%d - %H:%M:%S') + \
            ', date -> ' + self.date.strftime('%Y/%m/%d - %H:%M:%S') + \
            ', done -> ' + str(self.done)

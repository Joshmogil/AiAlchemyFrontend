from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String,  DateTime, Boolean
from sqlalchemy.orm import Session
import datetime

from app.database import Base


class ToDo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    session_key = Column(String)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

class TokenTable(Base):
    __tablename__ = "token"
    user_id = Column(Integer)
    access_toke = Column(String(450), primary_key=True)
    refresh_toke = Column(String(450),nullable=False)
    status = Column(Boolean)
    created_date = Column(DateTime, default=datetime.datetime.now)



def create_todo(db: Session, content: str, session_key: str):
    todo = ToDo(content=content, session_key=session_key)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def get_todo(db: Session, item_id: int):
    return db.query(ToDo).filter(ToDo.id == item_id).first()


def update_todo(db: Session, item_id: int, content: str):
    todo = get_todo(db, item_id)
    todo.content = content
    db.commit()
    db.refresh(todo)
    return todo


def get_todos(db: Session, session_key: str, skip: int = 0, limit: int = 100):
    return db.query(ToDo).filter(ToDo.session_key == session_key).offset(skip).limit(limit).all()


def delete_todo(db: Session, item_id: int):
    todo = get_todo(db, item_id)
    db.delete(todo)
    db.commit()
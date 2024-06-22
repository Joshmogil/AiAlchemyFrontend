from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy import Column, Integer, String
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./test.db"


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

class ToDo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    session_key = Column(String)


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

async def create_todo(content: str, session_key: str, session: AsyncSession = Depends(get_async_session)):
    todo = ToDo(content=content, session_key=session_key)
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return todo


async def get_todo(item_id: int, session: AsyncSession = Depends(get_async_session)) -> ToDo | None:
    stmt = select(ToDo).where(ToDo.id == item_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def update_todo(item_id: int, content: str, session: AsyncSession = Depends(get_async_session)):
    todo = await get_todo(item_id, session)
    if todo is None:
        return None
    todo.content = content # type: ignore
    await session.commit()
    await session.refresh(todo)
    return todo


async def get_todos(session_key: str, skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_async_session)):
    stmt = select(ToDo).where(ToDo.session_key == session_key).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_todo(item_id: int, session: AsyncSession = Depends(get_async_session)):
    todo = get_todo(item_id, session)
    await session.delete(todo)
    await session.commit()
    return todo
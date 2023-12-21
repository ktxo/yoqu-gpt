import asyncio
import json
import logging
import os

from sqlmodel import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from ktxo.yoqu.config import settings
from ktxo.yoqu.model import Messages

logger = logging.getLogger("ktxo.yoqu")

connect_args = {"check_same_thread": False}
engine = create_async_engine(settings.db_url, echo=False, connect_args=connect_args)


async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session


async def get_messages(session:AsyncSession,
                       id_: str = None,
                       resource_name: str = None,
                       name: str = None):
    async with session:
        filter_ = []
        if id_:
            filter_.append(Messages.id == id_)
        if resource_name:
            filter_.append(Messages.resource == resource_name)
        if name:
            filter_.append(Messages.name.like(f"%{name}%"))

        if filter_:
            messages = await session.execute(select(Messages).filter(and_(*filter_)))
        else:
            messages = await session.execute(select(Messages))
        rows = messages.fetchall()
        # :-((((
        rows = [row._asdict() for row in rows]
        for row in rows:
            row["created"] = str(row["Messages"].created)
            row["updated"] = str(row["Messages"].updated)
            row["messages"] = json.loads(row["Messages"].messages)
        return rows


async def add_message(session:AsyncSession,
                      message: Messages) -> Messages:
    #async with AsyncSession(engine, expire_on_commit=False) as session:
    try:
        async with session:
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message
    except Exception as e:
        logger.error(f"Encountered an error while accessing the DB. ({e})")
        return None

from ktxo.yoqu.model import RPAChat
async def add_message2(session:AsyncSession,
                      chat: RPAChat) -> Messages:
    #async with AsyncSession(engine, expire_on_commit=False) as session:
    try:
        async with session:
            session.add(chat)
            await session.commit()
            await session.refresh(chat)
            return chat
    except Exception as e:
        logger.error(f"Encountered an error while accessing the DB. ({e})")
        return None

async def update_message(session:AsyncSession,
                         id_: str,
                         resource_name: str = None,
                         type_: str = None,
                         messages: str = None,
                         deleted: bool = None) -> Messages:
    try:
        async with session:
            m: Messages = (await session.execute(select(Messages).filter(Messages.id == id_))).fetchone()
            if not m:
                return None
            m = m[0]
            if resource_name: m.resource = resource_name
            if type_:
                m.type = type_
            if messages:
                m.messages = messages
            if deleted is not None:
                m.deleted = deleted
            session.add(m)
            await session.commit()
            await session.refresh(m)
            return m
    except Exception as e:
        logger.error(f"Encountered an error while accessing the DB. ({e})")
        return None



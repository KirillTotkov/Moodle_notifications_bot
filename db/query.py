from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get(session: AsyncSession, model, **kwargs):
    return await session.execute(select(model).filter_by(**kwargs))


async def get_all(session: AsyncSession, model):
    return await session.execute(select(model))


async def add(session: AsyncSession, model, **kwargs):
    obj = model(**kwargs)
    session.add(obj)
    await session.commit()

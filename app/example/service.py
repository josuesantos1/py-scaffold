import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.example.model import Item, ItemCreate

logger = structlog.get_logger()


async def get_items(session: AsyncSession) -> list[Item]:
    result = await session.exec(select(Item))
    return list(result.all())


async def get_item(session: AsyncSession, item_id: int) -> Item | None:
    return await session.get(Item, item_id)


async def create_item(session: AsyncSession, payload: ItemCreate) -> Item:
    item = Item.model_validate(payload)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    logger.info("item_created", id=item.id, name=item.name)
    return item

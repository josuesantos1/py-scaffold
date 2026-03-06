import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.example import service
from app.example.model import Item, ItemCreate
from config.database import get_db

logger = structlog.get_logger()

router = APIRouter()


@router.get("/", response_model=list[Item])
async def list_items(session: AsyncSession = Depends(get_db)):
    return await service.get_items(session)


@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate, session: AsyncSession = Depends(get_db)):
    return await service.create_item(session, payload)


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int, session: AsyncSession = Depends(get_db)):
    item = await service.get_item(session, item_id)
    if not item:
        logger.warning("item_not_found", item_id=item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

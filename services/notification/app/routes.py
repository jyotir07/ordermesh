from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import Identity, require_role

from . import service
from .database import db
from .schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    _: Identity = Depends(require_role("ADMIN")),
    session: AsyncSession = Depends(db.session),
):
    return await service.list_notifications(session)

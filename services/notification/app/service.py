"""Notification handling: mock email delivery + persisted history."""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Notification

logger = logging.getLogger(__name__)


async def send_notification(
    session: AsyncSession,
    *,
    notification_type: str,
    recipient: str,
    payload: dict,
    order_id: int | None = None,
) -> Notification:
    """'Send' an email (mocked: logged) and persist the notification record."""
    logger.info(
        "EMAIL [%s] -> %s :: %s", notification_type, recipient, json.dumps(payload, default=str)
    )
    notification = Notification(
        type=notification_type,
        recipient=recipient,
        payload=json.dumps(payload, default=str),
        status="SENT",
        order_id=order_id,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification


async def list_notifications(session: AsyncSession, limit: int = 100) -> list[Notification]:
    stmt = select(Notification).order_by(Notification.id.desc()).limit(limit)
    return list(await session.scalars(stmt))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import Identity, get_identity

from . import service
from .database import cache, db
from .models import OrderStatus
from .schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


def _is_admin(identity: Identity) -> bool:
    return identity.role == "ADMIN"


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    identity: Identity = Depends(get_identity),
    session: AsyncSession = Depends(db.session),
):
    order = await service.create_order(session, int(identity.user_id), payload)
    return order


@router.get("", response_model=list[OrderOut])
async def list_orders(
    identity: Identity = Depends(get_identity),
    session: AsyncSession = Depends(db.session),
):
    customer_id = None if _is_admin(identity) else int(identity.user_id)
    return await service.list_orders(session, customer_id)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    identity: Identity = Depends(get_identity),
    session: AsyncSession = Depends(db.session),
):
    cached = await cache.get_json(f"order:{order_id}")
    if cached is not None:
        if not _is_admin(identity) and cached["customer_id"] != int(identity.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return cached

    order = await service.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not _is_admin(identity) and order.customer_id != int(identity.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    result = OrderOut.model_validate(order)
    await cache.set_json(f"order:{order_id}", result.model_dump())
    return result


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: int,
    identity: Identity = Depends(get_identity),
    session: AsyncSession = Depends(db.session),
):
    order = await service.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not _is_admin(identity) and order.customer_id != int(identity.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel an order in status {order.status}",
        )
    return await service.cancel_order(session, order)

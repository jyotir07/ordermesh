from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import Identity, get_identity, require_role

from . import service
from .database import cache, db
from .schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/inventory/products", tags=["inventory"])


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    _: Identity = Depends(require_role("ADMIN")),
    session: AsyncSession = Depends(db.session),
):
    try:
        product = await service.create_product(session, payload)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")
    return product


@router.get("", response_model=list[ProductOut])
async def list_products(
    _: Identity = Depends(get_identity),
    session: AsyncSession = Depends(db.session),
):
    return await service.list_products(session)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    _: Identity = Depends(get_identity),
    session: AsyncSession = Depends(db.session),
):
    cached = await cache.get_json(f"product:{product_id}")
    if cached is not None:
        return cached
    product = await service.get_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    result = ProductOut.model_validate(product)
    await cache.set_json(f"product:{product_id}", result.model_dump())
    return result

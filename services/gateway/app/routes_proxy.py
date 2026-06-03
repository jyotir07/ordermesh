"""Public routing surface. Authenticated requests are proxied to internal
services; admin-only operations are enforced here at the edge.
"""

from fastapi import APIRouter, Depends, Request, Response

from shared.auth import TokenData

from .config import settings
from .dependencies import current_user, require_admin
from .proxy import forward

router = APIRouter()


# --- Orders -------------------------------------------------------------------
@router.api_route("/orders", methods=["GET", "POST"], tags=["orders"])
async def orders_collection(request: Request, user: TokenData = Depends(current_user)):
    return await forward(request, settings.order_service_url, "/orders", user)


@router.api_route("/orders/{order_id}", methods=["GET"], tags=["orders"])
async def order_item(order_id: int, request: Request, user: TokenData = Depends(current_user)):
    return await forward(request, settings.order_service_url, f"/orders/{order_id}", user)


@router.api_route("/orders/{order_id}/cancel", methods=["POST"], tags=["orders"])
async def order_cancel(order_id: int, request: Request, user: TokenData = Depends(current_user)):
    return await forward(
        request, settings.order_service_url, f"/orders/{order_id}/cancel", user
    )


# --- Inventory ----------------------------------------------------------------
@router.api_route("/inventory/products", methods=["GET"], tags=["inventory"])
async def list_products(request: Request, user: TokenData = Depends(current_user)):
    return await forward(
        request, settings.inventory_service_url, "/inventory/products", user
    )


@router.api_route("/inventory/products", methods=["POST"], tags=["inventory"])
async def create_product(request: Request, user: TokenData = Depends(require_admin)):
    return await forward(
        request, settings.inventory_service_url, "/inventory/products", user
    )


# --- Shipping -----------------------------------------------------------------
@router.api_route("/shipments/{shipment_id}", methods=["GET"], tags=["shipping"])
async def get_shipment(shipment_id: int, request: Request, user: TokenData = Depends(current_user)):
    return await forward(
        request, settings.shipping_service_url, f"/shipments/{shipment_id}", user
    )

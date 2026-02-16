from fastapi import APIRouter

from app.api.v1.endpoints import affiliates, auth, orders, products

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(affiliates.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)

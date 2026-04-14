from fastapi import APIRouter
from app.api.v1.endpoints import auth, products, users

# Router principal de la versión 1 de la API
api_router = APIRouter()

# Módulo de autenticación
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Módulo de usuarios
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# Módulo de productos
api_router.include_router(
    products.router,
    prefix="/products",
    tags=["products"]
)
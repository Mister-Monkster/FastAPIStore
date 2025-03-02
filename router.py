import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from payment_system import make_payment
from product_service import ProductService
from queries import add_product, add_key, select_key, get_prod_by_id, payment_save
from schemas import ProductPost, KeysPost, ProductsGet, KeysGet, PaymentsPost

logger = logging.getLogger('api')


async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def get_redis():
    redis = Redis.from_url("redis://localhost:6379",
                           decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()


RedisDep = Annotated[Redis, Depends(get_redis)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(
    prefix="",
    tags=["Магазин"],
)


async def get_product_service(
    session: SessionDep,
    redis: RedisDep
) -> ProductService:
    return ProductService(session, redis)


ProductServiceDep = Depends(get_product_service)


@router.post("/add_products")
async def new_product(product: Annotated[ProductPost, Query()], session: SessionDep):
    result = await add_product(product, session)
    return result


@router.post("/add_keys")
async def new_key(keys: Annotated[KeysPost, Query()], session: SessionDep):
    result = await add_key(keys, session)
    return result


@router.get("/get_products")
async def products(category,
                   limit: int = 3,
                   offset: int = 0,
                    service: ProductService = ProductServiceDep
                   ) -> list[ProductsGet]:
    result = await service.get_products(category, limit, offset)
    return result


@router.get("/get_all_products")
async def all_products(limit: int = 3,
                       offset: int = 0,
                       service: ProductService = ProductServiceDep) -> list[ProductsGet]:
    result = await service.get_all_products(limit, offset)
    return result


@router.get("/get_keys")
async def get_keys(product_id: int, session: SessionDep) -> list[KeysGet]:
    res = await select_key(product_id, session)
    return res


@router.post("/post_keys_from_file")
async def post_keys_from_file(filename: str, product_id: int, session: SessionDep):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        for line in lines:
            if line:
                key = KeysPost.model_validate({'item': line, "product_id": product_id})
                await add_key(key, session)
        os.remove(filename)
        return {"ok: True"}


@router.post("/payments")
async def payment(product_id: int, user_id: int, session: SessionDep):
    product = await get_prod_by_id(product_id, session)
    res = await make_payment(product=product, user_id=user_id)
    return res


@router.post("/save-payments")
async def payments_save(payment: PaymentsPost, session: SessionDep):
    await payment_save(payment, session)
    return {"ok": True}

import os
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from payment_system import make_payment

from queries import add_product, add_key, select_products, select_key, get_prod_by_id, payment_save, select_all_products
from schemas import ProductPost, KeysPost, ProductsGet, KeysGet, PaymentsPost


async def get_session():
    async with async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(
    prefix="",
    tags=["Магазин"],
)


@router.post("/add_products")
async def new_product(product: Annotated[ProductPost, Query()], session: SessionDep):
    result = await add_product(product, session)
    return result


@router.post("/add_keys")
async def new_key(keys: Annotated[KeysPost, Query()], session: SessionDep):
    result = await add_key(keys, session)
    return result


@router.get("/get_products")
async def products(session: SessionDep, category, limit: int = 3, offset: int = 0) -> list[ProductsGet]:
    result = await select_products(session, category, limit, offset)
    return result


@router.get("/get_all_products")
async def all_products(session: SessionDep, limit: int = 3, offset: int = 0) -> list[ProductsGet]:
    result = await select_all_products(session, limit, offset)
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

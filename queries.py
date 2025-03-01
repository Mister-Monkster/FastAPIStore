from fastapi import HTTPException
from sqlalchemy import select, func, asc

from models import ProductsModel, KeysModel, PaymentsModel
from schemas import ProductsGet, KeysGet, PaymentsPost


async def add_product(product, session):
    product_dict = product.model_dump()
    new_product = ProductsModel(**product_dict)
    session.add(new_product)
    await session.commit()
    return {'ok': True}


async def select_products(session, category, limit, offset) -> list[ProductsGet]:
    query = (
        select(ProductsModel, func.count(KeysModel.id))
        .join(KeysModel, ProductsModel.id == KeysModel.product_id)
        .where(ProductsModel.category == category)
        .group_by(ProductsModel.id)
        .having(func.count(KeysModel.id) > 0)
        .order_by(asc(ProductsModel.id))
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(query)
    products = result.all()
    res = []
    for product in products:
        model_dict = product[0].as_dict_with_remainder()
        model_dict['remainder'] = product[1]
        res.append(model_dict)
    products_schema = [ProductsGet.model_validate(product) for product in res]
    return products_schema


async def select_all_products(session, limit, offset) -> list[ProductsGet]:
    query = (
        select(ProductsModel, func.count(KeysModel.id))
        .join(KeysModel, ProductsModel.id == KeysModel.product_id, isouter=True)
        .group_by(ProductsModel.id)
        .order_by(asc(ProductsModel.id))
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(query)
    products = result.all()
    res = []
    for product in products:
        print(product)
        model_dict = product[0].as_dict_with_remainder()
        model_dict['remainder'] = product[1]
        res.append(model_dict)

    products_schema = [ProductsGet.model_validate(product) for product in res]
    return products_schema


async def total_rows(model, session):
    row_count = func.count(ProductsModel.id)
    rows = await session.execute(row_count)
    rows = rows.scalars().one()
    return rows


async def add_key(key, session):
    key_dict = key.model_dump()
    new_key = KeysModel(**key_dict)
    try:
        session.add(new_key)
        await session.commit()
        return {'ok': True}
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))


async def select_key(product_id: int, session) -> list[KeysGet]:
    query = select(KeysModel).where(KeysModel.product_id == product_id)
    result = await session.execute(query)
    res = result.scalars().first()
    if res:
        await session.delete(res)
        await session.commit()
        KeysGet.model_validate(res)
        return [res]
    else:
        raise HTTPException(status_code=404, detail='No keys.')


async def get_prod_by_id(product_id: int, session) -> ProductsGet:
    query = select(ProductsModel).where(ProductsModel.id == product_id)
    result = await session.execute(query)
    res = result.scalars().one()
    return res


async def payment_save(payment: PaymentsPost, session):
    payment_schema = PaymentsPost.model_validate(payment)
    new_payment = PaymentsModel(**payment)
    session.add(new_payment)
    await session.commit()



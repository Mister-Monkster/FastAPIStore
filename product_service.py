import json

from redis.asyncio import Redis
from sqlalchemy import select, func, asc
from sqlalchemy.ext.asyncio import AsyncSession

from models import ProductsModel, KeysModel
from schemas import ProductsGet


class ProductService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.session = session
        self.redis = redis

    async def get_products(
            self,
            category: str,
            limit: int = 3,
            offset: int = 0
    ) -> list[ProductsGet]:
        cache_key = f"products:{category}:{limit}:{offset}"

        if cached := await self.redis.get(cache_key):
            return json.loads(cached)

        result = await self._fetch_from_db(category, limit, offset)

        result_json = json.dumps([item.model_dump() for item in result])
        await self.redis.setex(cache_key, 300, result_json)
        return result

    async def _fetch_from_db(self, category: str, limit: int, offset: int):
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
        result = await self.session.execute(query)
        products = result.all()
        res = []
        for product in products:
            model_dict = product[0].as_dict_with_remainder()
            model_dict['remainder'] = product[1]
            res.append(model_dict)
        products_schema = [ProductsGet.model_validate(product) for product in res]
        return products_schema

    async def get_all_products(self, limit: int = 3, offset: int = 0) -> list[ProductsGet]:
        cache_key = f'products:{limit}:{offset}'

        if cached := await self.redis.get(cache_key):
            return json.loads(cached)

        db_result = await self.fetch_all_products(limit, offset)

        serialized = json.dumps([item.dict() for item in db_result])
        await self.redis.setex(cache_key, 300, serialized)
        return db_result

    async def fetch_all_products(self, limit: int, offset: int) -> list[ProductsGet]:
        query = (
            select(ProductsModel, func.count(KeysModel.id))
            .join(KeysModel, ProductsModel.id == KeysModel.product_id, isouter=True)
            .group_by(ProductsModel.id)
            .order_by(asc(ProductsModel.id))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        products = result.all()
        res = []
        for product in products:
            print(product)
            model_dict = product[0].as_dict_with_remainder()
            model_dict['remainder'] = product[1]
            res.append(model_dict)

        products_schema = [ProductsGet.model_validate(product) for product in res]
        return products_schema

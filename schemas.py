
from pydantic import BaseModel, UUID1


class ProductPost(BaseModel):
    title: str
    description: str
    price: int
    category: str
    image: str


class ProductsGet(ProductPost):
    id: int
    remainder: int


class KeysGet(BaseModel):
    item: str

    class Config:
        from_attributes = True


class KeysPost(KeysGet):
    product_id: int


class PaymentsPost(BaseModel):
    uuid: UUID1
    user_id: int
    product_id: int
    status: str



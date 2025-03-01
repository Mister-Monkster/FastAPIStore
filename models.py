import datetime
import enum
from typing import Annotated

from pydantic import UUID1
from sqlalchemy import ForeignKey, String, CheckConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

intpk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]


class Categories(enum.Enum):
    games = "games"
    subs = "subs"
    accounts = "accounts"


class Model(DeclarativeBase):
    pass


class ProductsModel(Model):
    __tablename__ = "products"

    id: Mapped[intpk]
    title: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(512))
    category: Mapped[Categories]
    price: Mapped[int] = mapped_column(nullable=False)
    keys: Mapped[list['KeysModel']] = relationship(back_populates="product")
    payments: Mapped[list['PaymentsModel']] = relationship(back_populates='product')
    image: Mapped[str]

    __table_args__ = (
        CheckConstraint("price > 0", name="checl_price_positive"),
    )

    def as_dict_with_remainder(self):
        res = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        res['remainder'] = 0
        return res


class KeysModel(Model):
    __tablename__ = "keys"

    id: Mapped[intpk]
    item: Mapped[str] = mapped_column(unique=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete="CASCADE"))
    product: Mapped[list['ProductsModel']] = relationship(back_populates="keys")


class PaymentsModel(Model):
    __tablename__ = "payments"

    uuid: Mapped[UUID1] = mapped_column(primary_key=True)
    user_id: Mapped[int]
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    product: Mapped[list['ProductsModel']] = relationship(back_populates="payments")
    date: Mapped[created_at]
    status: Mapped[str]


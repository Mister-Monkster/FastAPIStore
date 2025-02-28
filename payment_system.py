import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from yoomoney import Authorize, Quickpay
from dotenv import load_dotenv
import os
from yoomoney import Client
import requests

from models import PaymentsModel
from queries import payment_save

from schemas import ProductsGet, PaymentsPost

load_dotenv()

client_id = os.getenv("YOO_CLIENT_ID")
O2Auth = os.getenv("YOO_O2AUTH")
redirect_uri = "https://yoomoney.ru"


token = os.getenv('YOO_TOKEN')
client = Client(token)


async def make_payment(product: ProductsGet, user_id):
    label = uuid.uuid1()
    quickpay = Quickpay(
                receiver=os.getenv("RECIVER"),
                quickpay_form="shop",
                targets=f"{product.title}",
                paymentType="SB",
                comment=f'{label}',
                sum=product.price,
                label=label,

                )

    return {
        "URL": quickpay.redirected_url,
        "product": product,
        "label": label
    }


async def check_status(label, user_id, product_id, session):
    payment_rep = {
        "uuid": label,
        "user_id": user_id,
        "product_id": product_id,
    }
    history = client.operation_history(label=label)
    for operation in history.operations:
        payment_rep['status'] = operation.status
        await payment_save(payment_rep, session)
        return True





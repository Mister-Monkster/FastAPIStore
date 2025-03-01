import asyncio
import logging
import os
import uuid
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from database import async_session
from middleware import DatabaseMiddleware
from product_service import ProductService
from router import products
from telegram_router import router, bot

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")


dp = Dispatcher()
dp.update.middleware(DatabaseMiddleware(session_pool=async_session))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(os.name)





async def run_bot():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
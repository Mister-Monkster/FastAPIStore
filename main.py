from fastapi import FastAPI

from router import router
from fastapi import FastAPI

from router import router

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await delete_tables()
#     print('База очищена')
#     await create_tables()
#     print('База готова к работе')
#     yield
#     print("Выключение")lifespan=lifespan

app = FastAPI()

app.include_router(router)
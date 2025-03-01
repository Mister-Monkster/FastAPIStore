import os
import uuid

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from models import ProductsModel
from payment_system import check_status
from queries import total_rows
from router import new_product, payment, get_keys, post_keys_from_file
from schemas import ProductPost
from utils import delete_old, page_view, all_page_view, get_all_products_for_bot, get_products_for_bot

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
router = Router()
whitelist = [5863456999]


class AddProductState(StatesGroup):
    title = State()
    description = State()
    category = State()
    price = State()
    image = State()


class Pages(StatesGroup):
    total = State()
    messages = State()
    category = State


class AddKeys(StatesGroup):
    file = State()
    product_id = State()


@router.message(Command('start'))
async def start_handler(message: Message):
    inline_kb_list = [
        [InlineKeyboardButton(text='Игры', callback_data=f'catalog_games')],
        [InlineKeyboardButton(text='Подписки', callback_data=f'catalog_subs')],
        [InlineKeyboardButton(text='Аккаунты', callback_data=f'catalog_accounts')],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
    text = ("Привет в этом боте ты можешь приобрести различные цифровые товары.\n"
            "Выбери категорию и я предоставлю тебе каталог.")
    await message.answer(text, reply_markup=kb)


@router.message(Command('add_keys'))
async def add_keys_handler(message: Message, state: FSMContext, session: AsyncSession):
    if message.from_user.id not in whitelist:
        return None
    total_pages = (await total_rows(ProductsModel, session) + 2) // 3
    offset = 0
    chat_id = message.chat.id
    data = await get_all_products_for_bot(offset=offset)
    messages = await all_page_view(bot, data, chat_id, total_pages, offset, offset)
    await state.update_data(total=total_pages, messages=messages)


@router.callback_query(F.data.startswith('all_pages_'))
async def page_handler(call: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    page_num = int(call.data.split('all_pages_')[1])
    total_pages = state_data['total']
    chat_id = call.message.chat.id
    offset = page_num * 3
    data = await get_all_products_for_bot(offset=offset)
    messages = state_data['messages']
    await delete_old(chat_id, messages, bot)
    messages = await all_page_view(bot, data, chat_id, total_pages, page_num, offset)
    await state.update_data(messages=messages)


@router.callback_query(F.data.startswith('pick_'))
async def add_keys_callback(call: CallbackQuery, state: FSMContext):
    product_id = call.data.split('pick_')[1]
    await bot.send_message(call.message.chat.id, 'Отправьте текстовый файл с ключами')
    await state.set_state(state=AddKeys.file)
    await state.update_data(product_id=int(product_id))


@router.message(StateFilter(AddKeys.file))
async def add_keys_file(message: Message, state: FSMContext, session: AsyncSession):
    directory = f'key_files/{message.document.file_name}'
    data = await state.get_data()
    product_id = data['product_id']
    await bot.download(file=message.document, destination=directory)
    await post_keys_from_file(directory, product_id, session)
    await state.clear()


@router.message(Command('add_product'))
async def add_product_handler(message: Message, state: FSMContext):
    if message.from_user.id not in whitelist:
        return None
    await state.set_state(state=AddProductState.title)
    await message.answer('Введите название товара')


@router.message(StateFilter(AddProductState.title))
async def add_product_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddProductState.description)
    await message.answer('Напишите описание товара')


@router.message(StateFilter(AddProductState.description))
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProductState.category)
    categories_list = ["Игры", "Aккаунты", "Подписки"]
    kb = [[KeyboardButton(text=i)] for i in categories_list]
    kb = ReplyKeyboardMarkup(keyboard=kb)
    await message.answer('Выберете категорию', reply_markup=kb)


@router.message(StateFilter(AddProductState.category))
async def add_product_description(message: Message, state: FSMContext):
    categories = {
        "Игры": "games",
        "Подписки": "subs",
        "Aккаунты": "accounts"
    }
    await state.update_data(category=categories[message.text])
    await message.answer("Введите цену в рублях", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddProductState.price)


@router.message(StateFilter(AddProductState.price))
async def add_product_price(message: Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(price=message.text)
        await message.answer('Отправьте мне изображение для товара')
        await state.set_state(AddProductState.image)
    else:
        await message.answer('Цена должна быть числом')


@router.message(F.photo, StateFilter(AddProductState.image))
async def add_product_photo(message: Message, state: FSMContext, session: AsyncSession):
    directory = f'images/{uuid.uuid1()}.png'
    await state.update_data(image=directory)
    data = await state.get_data()
    product = ProductPost.model_validate(data)
    await new_product(product, session)
    await message.answer("Товар успешно добавлен!")
    await state.clear()
    await message.bot.download(file=message.photo[-1].file_id, destination=directory)


@router.message(StateFilter(AddProductState.image))
async def is_photo(message: Message):
    await message.answer('Это не изображение!\nОтправьте мне изображение.')


@router.callback_query(F.data.startswith('catalog_'))
async def catalog(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    category = call.data.split('catalog_')[1]
    total_pages = (await total_rows(ProductsModel, session) + 2) // 3
    offset = 0
    chat_id = call.message.chat.id
    data = await get_products_for_bot(category, offset)
    messages = await page_view(bot, data, chat_id, total_pages, offset, offset)
    await state.update_data(total=total_pages, messages=messages, category=category)


@router.callback_query(F.data.startswith('page_'))
async def page_handler(call: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    page_num = int(call.data.split('page_')[1])
    total_pages = state_data['total']
    category = state_data['category']
    chat_id = call.message.chat.id
    offset = page_num * 3
    data = await get_products_for_bot(category, offset=offset)
    messages = state_data['messages']
    await delete_old(chat_id, messages, bot)
    messages = await page_view(bot, data, chat_id, total_pages, page_num, offset)
    await state.update_data(messages=messages)


@router.callback_query(F.data == 'delete_list')
async def delete_catalog(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        data = data['messages']
        chat_id = call.message.chat.id
        await delete_old(chat_id, data, bot)
        await state.clear()
    except:
        await call.answer('К сожалению я не могу удалить эти сообщения')


@router.callback_query(F.data.startswith('buy_'))
async def buy_product(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    data = data['messages']
    chat_id = call.message.chat.id
    await delete_old(chat_id, data, bot)
    await state.clear()
    product_id = int(call.data.split('buy_')[1])
    res = await payment(product_id, user_id=call.from_user.id, session=session)
    product = res["product"]
    inline_kb_list = [
        [InlineKeyboardButton(text='Оплатиь с помощью yoomoney', url=res["URL"])],
        [InlineKeyboardButton(text='Проверить статус', callback_data=f'check_{res['label']}_{product.id}')]
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
    text = f'Покупка товара:\n<b>{product.title}\n\nСтоимость - {product.price}RUB</b>'
    await bot.send_message(call.message.chat.id, text=text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith('check_'))
async def check(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    label = uuid.UUID(call.data.split('_')[1])
    prodict_id = int(call.data.split('_')[2])
    user_id = call.from_user.id
    res = await check_status(label, user_id, prodict_id, session)
    if res:
        key = await get_keys(prodict_id, session)
        await bot.send_message(f'Вы успешно оплатили товар, вот ваш ключ:\n<blockquote>{key}</blockquote>')
    else:
        await call.answer('Оплата еще не прошла, возможны задержки.\nПовторите попытку позже.', show_alert=True)

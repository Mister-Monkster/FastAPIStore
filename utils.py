from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from schemas import ProductsGet


async def delete_old(chat_id, messages: list, bot):
    ids = []
    for mess in messages:
        ids.append(mess.message_id)
    await bot.delete_messages(chat_id, ids)


async def page_view(bot, data, chat_id, total_pages, page_num, offset):
    messages = []
    if data:
        for product in data:
            if not isinstance(product, dict):
                product_dict = product.model_dump()
            else:
                product_dict = product
            image = FSInputFile(product_dict['image'])
            text = (f"<b>{product_dict['title']}</b>\n"
                    f"{product_dict['description']}\n\n"
                    f"Цена: {product_dict['price']}RUB\n"
                    f"Коллиество штук {product_dict['remainder']}"
                    )
            inline_kb_list = [
                [InlineKeyboardButton(text='Купить', callback_data=f'buy_{product_dict['id']}')]

            ]
            if (page_num + 1 == total_pages) and (len(messages) == len(data) - 1):
                inline_kb_list.append([InlineKeyboardButton(text="Предыдущая страница",
                                                            callback_data=f'page_{page_num - 1}')])
                inline_kb_list.append([InlineKeyboardButton(text="Убрать список",
                                                            callback_data=f'delete_list')])
            elif ((page_num + 1) < total_pages and (page_num + 1) != 1) and (len(messages) == len(data) - 1):
                inline_kb_list.append([InlineKeyboardButton(text="Cледующая страница",
                                                            callback_data=f'page_{page_num + 1}')])
                inline_kb_list.append([InlineKeyboardButton(text="Предыдущая страница",
                                                            callback_data=f'page_{page_num - 1}')])
                inline_kb_list.append([InlineKeyboardButton(text="Убрать список",
                                                            callback_data=f'delete_list')])
            elif len(messages) == len(data) - 1:
                    inline_kb_list.append([InlineKeyboardButton(text="Cледующая страница",
                                                                callback_data=f'page_{offset + 1}')])
                    inline_kb_list.append([InlineKeyboardButton(text="Убрать список",
                                                                callback_data=f'delete_list')])
            else:
                inline_kb_list.append([InlineKeyboardButton(text="Убрать список",
                                                            callback_data=f'delete_list')])

            kb = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
            mess = await bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb)

            messages.append(mess)
        return messages
    else:
        await bot.send_message(chat_id, "В данной категории отсутствуют товары. Возможно они появятся позже")


async def all_page_view(bot,  data, chat_id, total_pages, page_num, offset):
    messages = []
    if data:
        for product in data:
            if not isinstance(product, dict):
                product_dict = product.model_dump()
            else:
                product_dict = product
            image = FSInputFile(product_dict['image'])
            text = (f"<b>{product_dict['title']}</b>\n"
                    f"{product_dict['description']}\n\n"
                    f"Цена: {product_dict['price']}RUB\n"
                    f"Коллиество штук {product_dict['remainder']}"
                    )
            inline_kb_list = [
                [InlineKeyboardButton(text='Выбрать', callback_data=f'pick_{product_dict['id']}')]

            ]
            if (page_num + 1 == total_pages) and (len(messages) == len(data) - 1):
                inline_kb_list.append([InlineKeyboardButton(text="Предыдущая страница",
                                                            callback_data=f'all_pages_{page_num - 1}')])
                inline_kb_list.append([InlineKeyboardButton(text="Убрать список",
                                                            callback_data=f'delete_list')])
            elif ((page_num + 1) < total_pages and (page_num + 1) != 1) and (len(messages) == len(data) - 1):
                inline_kb_list.append([InlineKeyboardButton(text="Cледующая страница",
                                                            callback_data=f'page_{page_num + 1}')])
                inline_kb_list.append([InlineKeyboardButton(text="Предыдущая страница",
                                                            callback_data=f'all_pages_{page_num - 1}')])
                inline_kb_list.append([InlineKeyboardButton(text="Убрать список",
                                                            callback_data=f'delete_list')])
            elif len(messages) == len(data) - 1:
                inline_kb_list.append([InlineKeyboardButton(text="Cледующая страница",
                                                            callback_data=f'all_pages_{offset + 1}')])
                inline_kb_list.append([InlineKeyboardButton(text="Убрать список",
                                                            callback_data=f'delete_list')])

            kb = InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
            mess = await bot.send_photo(
                    chat_id=chat_id,
                    photo=image,
                    caption=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kb)

            messages.append(mess)
        return messages
    else:
        await bot.send_message(chat_id, "В данной категории отсутствуют товары. Возможно они появятся позже")




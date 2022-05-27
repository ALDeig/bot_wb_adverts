from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InputFile, InputMediaPhoto
from httpx import AsyncClient
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.keyboards import kb_user
from tgbot.services import db_queries 
from tgbot.services.wb import wb, common, errors
from tgbot.services.texts import Texts


# media_group 13222269398378458
# AgACAgIAAxkDAAIgsmKDfZ7b8guXaHGMQGyfU9T3_E1uAAK6ujEbViEZSCve-ONW0q7HAQADAgADeQADJAQ 
# AgACAgIAAxkDAAIgs2KDfZ7OX0YxY8CuafdqFZOGCzIPAAK7ujEbViEZSJX6JnsT1RbZAQADAgADeQADJAQ
# AQADu7oxG1YhGUh-


async def user_start(msg: Message, db: AsyncSession, state: FSMContext):
    """Обработка команды старт"""
    await state.finish()
    user = await db_queries.get_user(db, msg.from_user.id)
    if not user:
        # images = [InputMediaPhoto(InputFile("images/1.jpg")), InputMediaPhoto(InputFile("images/2.jpg"))]
        images = [
            InputMediaPhoto("AgACAgIAAxkDAAIgsmKDfZ7b8guXaHGMQGyfU9T3_E1uAAK6ujEbViEZSCve-ONW0q7HAQADAgADeQADJAQ"),
            InputMediaPhoto("AgACAgIAAxkDAAIgs2KDfZ7OX0YxY8CuafdqFZOGCzIPAAK7ujEbViEZSJX6JnsT1RbZAQADAgADeQADJAQ")
        ]
        await msg.answer(Texts.start)
        await msg.answer_media_group(images)
        await msg.answer("Оформить подписку", reply_markup=kb_user.subscribe())
        return
    await msg.answer("Узнать ставки", reply_markup=kb_user.menu)


async def btn_subscribe(call: CallbackQuery):
    """Обработка команды на покупку подписки"""
    await call.answer()
    period = "день" if call.data == "day" else "месяц"
    await call.message.answer(f"Вы выбрали 1 {period} подписки")
    await call.message.answer(Texts.subscribe, reply_markup=kb_user.paid())


async def paid(call: CallbackQuery):
    """Обработка команды 'Оплатил'. """
    await call.answer()
    await call.message.edit_reply_markup()
    await call.message.answer(Texts.paid, reply_markup=kb_user.menu)


async def btn_check_price_in_search(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    """Откликается на кнопку 'Поиск'"""
    await call.answer()
    user = await db_queries.get_user(db, call.from_user.id)
    if not user:
        await call.message.answer(Texts.start)
        return
    await call.message.edit_text("Введите поисковый запрос")
    await state.set_state("get_search_query")


async def get_search_query(msg: Message, state: FSMContext):
    """Получает поисковый запрос для проверки цены на рекламу"""
    try:
        headers = common.get_headers()
        async with AsyncClient(headers=headers, timeout=common.TIMEOUT) as client:
            result = await wb.get_adverts_by_query_search(client, msg.text.lower())
    except errors.BadRequestInWB:
        await msg.answer("Не удалось обработать запрос. Возможно неверный поисковый запрос")
        await state.finish()
        return
    kb = kb_user.subscribe_to_update_price("text")
    # text_positions = "\n".join(f"{price.position} - {price.price} руб." for price in prices)
    # text = f"Ваш запрос: <b>{msg.text}</b>\n\nПозиции и цена:\n<u>{text_positions}</u>" 
    await msg.answer(result, reply_markup=kb)
    await msg.answer("Узнать ставки", reply_markup=kb_user.menu)
    await state.finish()


async def btn_check_price_in_card(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    """Реагирует на кнопку 'Карточка товара'"""
    await call.answer()
    user = await db_queries.get_user(db, call.from_user.id)
    if not user:
        await call.message.answer(Texts.start)
        return
    await call.message.answer("Введите артикул конкурента")
    await state.set_state("get_scu")


async def get_scu_for_get_price(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        await msg.answer("Артикул должен быть числом")
        return
    try:
        headers = common.get_headers()
        async with AsyncClient(headers=headers, timeout=common.TIMEOUT) as client:
            result = await wb.get_adverts_by_scu(client, msg.text)
    except Exception as e:
        logger.error(e)
        return
    kb = kb_user.subscribe_to_update_price("scu")
    await msg.answer(result, reply_markup=kb)
    await msg.answer("Узнать ставки", reply_markup=kb_user.menu)
    await state.finish()


async def btn_subscribe_to_update(call: CallbackQuery, db: AsyncSession, state: FSMContext):
    """Реагирует на кнопку подписки на отслеживание цены"""
    await call.answer()
    text_or_scu = call.message.text.split("\n\n")[0].split(":")[1].strip()
    type_query = call.data.split(":")[-1]
    # try:
    #     prices = await wb.get_position_with_price(query.lower())
    # except wb.BadRequestInWB:
    #     await call.message.answer("Не удалось обработать запрос")
    #     await call.message.edit_reply_markup()
    #     return 
    if type_query == "text":
        await db_queries.add_new_tracking(db, call.from_user.id, query_text=text_or_scu.lower())
    else:
        await db_queries.add_new_tracking(db, call.from_user.id, scu=int(text_or_scu))
    await call.message.edit_text(call.message.text + "\n\nОтслеживается")
    await state.finish()


async def send_my_tracking(msg: Message, db: AsyncSession):
    """Реагирует на команду 'my_tracking'. Отправляет все отслеживания пользователя"""
    all_tracking = await db_queries.get_tracking_by_user_id(db, msg.from_user.id)
    if not all_tracking:
        await msg.answer("У вас нет ни одного отслеживания")
        return
    text = "Ваши отслеживания:\n"
    for tracking in all_tracking:
        text += f"{tracking.query_text if tracking.query_text else tracking.scu}\n"
    await msg.answer(text)
    await msg.answer("Узнать ставки", reply_markup=kb_user.menu)


# async def cmd_delete_tracking(msg: Message, state: FSMContext):
#     await msg.answer("Введите текст запроса, который больше не нужно отслеживать")
#     await state.set_state("get_tracking_text_for_delete")


# async def get_tracking_text_for_delete(msg: Message, db: AsyncSession, state: FSMContext):
#     await state.finish()
#     result = await db_queries.delete_tracking(db, msg.from_user.id, msg.text.lower())
#     if result:
#         await msg.answer("Готово")
#     else:
#         await msg.answer("Такого отслеживания нет. Чтобы посмотреть свои отлеживания введите команду /my_tracking")
#     await msg.answer("Выберите дейтсвие", reply_markup=kb_user.menu)


async def btn_unsubscribe(call: CallbackQuery, db: AsyncSession):
    """Кнопка для отмены отслеживания"""
    await call.answer()
    await call.message.edit_reply_markup()
    query = call.message.text.split("\n\n")[0].split(":")[1].strip()
    type_query = call.data.split(":")[-1]
    if type_query == "scu":
        await db_queries.delete_tracking(db, call.from_user.id, scu=int(query))
    else: 
        await db_queries.delete_tracking(db, call.from_user.id, query_text=query.lower())
    await call.message.delete_reply_markup()
    await call.message.answer("Выберите дейтсвие", reply_markup=kb_user.menu)


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_callback_query_handler(btn_subscribe, lambda call: call.data == "day" or call.data == "month")
    dp.register_callback_query_handler(paid, lambda call: call.data == "paid")
    dp.register_callback_query_handler(btn_check_price_in_search, text="ads_in_search")
    dp.register_message_handler(get_search_query, state="get_search_query")
    dp.register_callback_query_handler(btn_check_price_in_card, text="ads_in_card")
    dp.register_message_handler(get_scu_for_get_price, state="get_scu")
    dp.register_callback_query_handler(btn_unsubscribe, text_contains="unsubscribe", state="*")
    dp.register_callback_query_handler(btn_subscribe_to_update, text_contains="subscribe", state="*")
    # dp.register_callback_query_handler(select_position_to_update, state="select_position_to_update")
    # dp.register_message_handler(get_count, state="get_count")
    dp.register_message_handler(send_my_tracking, commands=["my_tracking"])
    # dp.register_message_handler(cmd_delete_tracking, commands=["delete_tracking"])
    # dp.register_message_handler(get_tracking_text_for_delete, state="get_tracking_text_for_delete")

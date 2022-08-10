import asyncio
import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils.exceptions import ChatNotFound, BotBlocked
from sqlalchemy.ext.asyncio.session import AsyncSession

from ..services import db_queries
from ..services.exceptions import CantAddPromoCode


async def begin_add_user(msg: Message, state: FSMContext):
    await msg.answer("Введи id пользователя")
    await state.set_state("get_id")


async def get_id_user(msg: Message, state: FSMContext):
    try:
        tg_id = int(msg.text)
    except ValueError:
        await msg.answer("Должны быть только цифры")
        return
    await state.update_data(telegram_id=tg_id)
    await msg.answer("Введи количество дней, на которое предоставлен доступ (Отправь только цифру. Если введешь 0, \
то пользователь будет добавлен на неограниченное количество дней)")
    await state.set_state("get_count_days")


async def get_count_days(msg: Message, db: AsyncSession, state: FSMContext):
    try:
        days = int(msg.text)
    except ValueError:
        await msg.answer("Неверный формат")
        return
    data = await state.get_data()
    # subscribe = None if days == 0 else date.today() + timedelta(days=days)
    result = await db_queries.add_user(db, data["telegram_id"], days)
    await state.finish()
    if not result:
        await msg.answer("Такой пользователь уже есть.")
        return
    await msg.answer("Готово")


async def begin_broadcaster(msg: Message, state: FSMContext):
    await msg.answer("Введи текст сообщения")
    await state.set_state("get_message")


async def sending_message(msg: Message, db: AsyncSession, state: FSMContext):
    await state.finish()
    users = await db_queries.get_users(db)
    for user in users:
        try:
            await msg.copy_to(user.id)
            await asyncio.sleep(1)
        except (ChatNotFound, BotBlocked) as er:
            logging.error(f"Не удалось отправить сообщение. Ошибка: {er}")
    await msg.answer("Готово")


async def get_count_users(msg: Message, db: AsyncSession):
    users = await db_queries.get_users(db)
    text = f"Количество пользователей: {len(users)}\n" + \
           "\n".join([f"{user.id} - {user.subscribe}" for user in users])
    await msg.answer(text)


async def delete_user(msg: Message, state: FSMContext):
    await msg.answer("Введи id пользователя")
    await state.set_state("get_id_for_delete")


async def get_id_for_delete(msg: Message, db: AsyncSession, state: FSMContext):
    await state.finish()
    try:
        result = await db_queries.delete_user(db, int(msg.text))
    except ValueError:
        await msg.answer("Введите только цифры")
        return
    if not result:
        await msg.answer("Такого пользователя нет")
    else:
        await msg.answer("Готово")


#  promo codes
async def cmd_add_promo_code(msg: Message, state: FSMContext):
    await msg.answer("Введите промокод")
    await state.set_state("insert_promo_code")


async def insert_promo_code(msg: Message, state: FSMContext):
    await state.update_data(promo_code=msg.text)
    await msg.answer("Введите id пользователя к которому привязан промокод")
    await state.set_state("get_id_user_for_promo_code")


async def get_id_user_for_promo_code(msg: Message, state: FSMContext):
    try:
        user_id = int(msg.text)
    except ValueError:
        await msg.answer("ID должен быть числом")
        return
    await state.update_data(user_id=user_id)
    await msg.answer("Введите процент скидки промокода (просто число)")
    await state.set_state("get_discount_size")


async def get_discount_size(msg: Message, db: AsyncSession, state: FSMContext):
    try:
        discount_size = int(msg.text)
    except ValueError:
        await msg.answer("Размер скидки должен быть числом")
        return
    data = await state.get_data()
    await state.finish()
    try:
        await db_queries.add_promo_code(
            session=db,
            code=data["promo_code"],
            user=data["user_id"],
            discount_size=discount_size
        )
    except CantAddPromoCode:
        await msg.answer("Не удалось добавить промокод. Такого пользователя нет.")
        return
    await msg.answer("Готово")


async def get_promo_codes(msg: Message, db: AsyncSession):
    codes = await db_queries.get_all_promo_code(db)
    if not codes:
        await msg.answer("В базе не промокодов")
        return
    text = "Промокоды:\n"
    for code in codes:
        text += f"Код: {code.code}\nПользователь: {code.user}\nИспользован: {code.amount_use}\n" \
                f"Размер скидки: {code.discount_size}\r\n\r\n"
    await msg.answer(text)


async def cmd_delete_promo_code(msg: Message, state: FSMContext):
    await msg.answer("Введите промокод для удаления")
    await state.set_state("get_promo_code_for_delete")


async def get_promo_code_for_delete(msg: Message, db: AsyncSession, state: FSMContext):
    await db_queries.delete_promo_code(db, msg.text)
    await state.finish()
    await msg.answer("Готово")

def register_admin(dp: Dispatcher):
    dp.register_message_handler(begin_add_user, commands=["add_user"], state="*", is_admin=True)
    dp.register_message_handler(cmd_add_promo_code, commands=["add_promo_code"], state="*", is_admin=True)
    dp.register_message_handler(get_promo_codes, commands=["get_promo_codes"], state="*", is_admin=True)
    dp.register_message_handler(cmd_delete_promo_code, commands=["delete_promo_code"], state="*", is_admin=True)
    dp.register_message_handler(get_id_user, state="get_id")
    dp.register_message_handler(get_count_days, state="get_count_days")
    dp.register_message_handler(begin_broadcaster, commands=["sending"], is_admin=True)
    dp.register_message_handler(sending_message, state="get_message")
    dp.register_message_handler(get_count_users, commands=["count"], is_admin=True)
    dp.register_message_handler(delete_user, commands=["delete_user"], is_admin=True)
    dp.register_message_handler(get_id_for_delete, state="get_id_for_delete")
    dp.register_message_handler(insert_promo_code, state="insert_promo_code")
    dp.register_message_handler(get_id_user_for_promo_code, state="get_id_user_for_promo_code")
    dp.register_message_handler(get_discount_size, state="get_discount_size")
    dp.register_message_handler(get_promo_code_for_delete, state="get_promo_code_for_delete")

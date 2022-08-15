from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio.session import AsyncSession

from tgbot.keyboards import kb_user
from tgbot.services.payment import Payment, check_payment_process
from tgbot.services import db_queries


async def btn_promo_code(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Введите промокод")
    await state.set_state("get_promo_code_from_user")


async def get_promo_code_from_user(msg: Message, db: AsyncSession, state: FSMContext):
    await state.finish()
    code = await db_queries.get_promo_code(db, msg.text)
    config = msg.bot.get("config")
    if not code:
        await msg.answer("Такого кода нет",
                         reply_markup=kb_user.subscribe(config.pay.price_month, config.pay.price_day))
        return
    await msg.answer(
        text="Оплатить подписку",
        reply_markup=kb_user.subscribe(
            price_month=int(config.pay.price_month - (config.pay.price_month * (code.discount_size / 100))),
            price_day=config.pay.price_day,
            code=code.code,
            with_promo_code=False
        )
    )

async def btn_subscribe(call: CallbackQuery, db: AsyncSession):
    await call.answer()
    # await state.finish()
    qiwi = call.bot.get("qiwi")
    period = "день" if call.data.startswith("day") else "месяц"
    code = call.data.split(":")[-1] if len(call.data.split(":")) == 3 else None
    payment = Payment(
        amount=int(call.data.split(":")[1]),
        comment=f"Один {period} подписки на бота с рекламными ставками WB",
        period=1 if call.data.startswith("day") else 30,
        qiwi=qiwi,
        code=code
    )
    payment_url = await payment.create_bill()
    await call.message.answer(f"Вы выбрали 1 {period} подписки. Для перехода к окну оплаты, нажмите \"Оплатить\".",
                              reply_markup=kb_user.pay(payment_url))
    await call.message.answer("Подтверждение оплаты занимает до 5 минут")
    await check_payment_process(call.from_user.id, db, call.bot, payment)


# async def btn_subscribe(call: CallbackQuery, db: AsyncSession, state: FSMContext):
#     await call.answer()
#     await state.finish()
#     qiwi = call.bot.get("qiwi")
#     period = "день" if call.data == "day" else "месяц"
#     payment = Payment(
#         amount=900 if call.data == "day" else 2900,
#         comment=f"Один {period} подписки на бота с рекламными ставками WB",
#         period=1 if call.data == "day" else 30,
#         qiwi=qiwi
#     )
#     payment_url = await payment.create_bill()
#     await call.message.answer(f"Вы выбрали 1 {period} подписки. Для перехода к окну оплаты, нажмите \"Оплатить\".",
#                               reply_markup=kb_user.pay(payment_url))
#     await call.message.answer("Подтверждение оплаты занимает до 5 минут")
#     await check_payment_process(call.from_user.id, db, call.bot, payment)


def register_payment(dp: Dispatcher):
    dp.register_callback_query_handler(btn_promo_code, text="promo_code")
    dp.register_message_handler(get_promo_code_from_user, state="get_promo_code_from_user")
    dp.register_callback_query_handler(btn_subscribe, text_startswith=["month", "day"])
    # dp.register_callback_query_handler(btn_subscribe, lambda call: call.data.startswith("day") or call.data.startswith("month"))


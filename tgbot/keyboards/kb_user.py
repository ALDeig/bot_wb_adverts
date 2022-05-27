from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.models.models import Price


menu = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton(text="Поиск", callback_data="ads_in_search"),
    InlineKeyboardButton(text="Карточка товара", callback_data="ads_in_card")
)


def subscribe():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="1 день 900р", callback_data="day"),
        InlineKeyboardButton(text="1 месяц 2900р", callback_data="month")
    )
    return kb


def paid():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Оплатил(а)", callback_data="paid")
    )
    return kb


def subscribe_to_update_price(query: str):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить в отслеживание", callback_data=f"subscribe:{query}")]
        ]
    )
    return kb


def unsubscribe(type_query: str):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Убрать из отслеживания", callback_data=f"unsubscribe:{type_query}")]
        ]
    )
    return kb


def select_position_for_subscribe(prices: list[Price]):
    kb = InlineKeyboardMarkup(row_width=1)
    for price in prices:
        kb.add(
            InlineKeyboardButton(
                text=f"{price.position} - {price.price}",
                callback_data=f"{price.position}:{price.price}"
            )
        )
    return kb

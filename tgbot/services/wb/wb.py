from json.decoder import JSONDecodeError

import httpx

from tgbot.models.models import AdsCard
from tgbot.services.wb.errors import BadRequestInWB
from tgbot.services.wb.common import TIMEOUT


async def get_adverts_by_query_search(client: httpx.AsyncClient, query: str) -> tuple:
    result = await client.get(
        url="https://catalog-ads.wildberries.ru/api/v5/search",
        params={"keyword": query},
        timeout=TIMEOUT
    )
    try:
        adverts = result.json()["adverts"]
        pages = result.json()["pages"]
    except (KeyError, IndexError, TypeError, JSONDecodeError):
        raise BadRequestInWB
    return adverts, pages


async def get_adverts_by_scu(client: httpx.AsyncClient, scu: str) -> str:
    list_ads_cards = await _get_list_ads_by_scu_from_wb(scu, client)
    prices_with_position = _group_position_by_price(list_ads_cards)
    text = _create_text_message_by_group_ads_card(prices_with_position, scu)
    return text


async def _get_list_ads_by_scu_from_wb(scu: str, client: httpx.AsyncClient) -> list[AdsCard]:
    """Возвращает данные по запросу в wb о рекламном блоке в карточке"""
    response = await client.get("https://carousel-ads.wildberries.ru/api/v4/carousel", params={"nm": scu})
    return [AdsCard.parse_obj(card) for card in response.json()]


def _group_position_by_price(list_ads_cards: list[AdsCard]) -> dict:
    result = {}
    for card in list_ads_cards:
        if card.price in result:
            result[card.price].append(card.position)
        else:
            result[card.price] = [card.position]
    return result


def _create_text_message_by_group_ads_card(prices_with_position: dict[int,list], scu: int | str) -> str:
    text = "Карточка с артикулом: " + str(scu) + "\n"
    for price, position in prices_with_position.items():
        if len(position) > 1:
            text += f"\nПозиции {position[0]}-{position[-1]}: {price}"
        else:
            text += f"\nПозиция {position[0]}: {price}"
    return text


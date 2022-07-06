from json.decoder import JSONDecodeError

import httpx

from tgbot.models.models import Price, AdsCard
from tgbot.services.wb.errors import BadRequestInWB
from tgbot.services.wb.common import TIMEOUT, get_headers


# for test
# from pydantic import BaseModel, Field
# from errors import BadRequestInWB
# from common import TIMEOUT, get_headers
# 
# 
# class AdsCard(BaseModel):
#     scu: int = Field(alias="nmId") 
#     position: int
#     price: int = Field(alias="cpm")
# 
# 
# class Price(BaseModel):
#     scu: int
#     position: int
#     price: int

# end test


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


async def get_adverts_by_scu(client: httpx.AsyncClient, scu: str) -> str:
    list_ads_cards = await _get_list_ads_by_scu_from_wb(scu, client)
    prices_with_position = _group_position_by_price(list_ads_cards)
    text = _create_text_message_by_group_ads_card(prices_with_position, scu)
    return text



def _parse_adverts_to_positions(all_ads_card: dict, positions: list[int]):
    adverts = []
    for index, position in enumerate(positions):
        # index = position - 1 if positions[0] == 1 else position - positions[0]
        try:
            adverts.append(Price(
                scu=all_ads_card["adverts"][index]["id"],
                position=position,
                price=all_ads_card["adverts"][index]["cpm"]
            ))
        except IndexError:
            raise BadRequestInWB
    return adverts


def _create_text_message_by_query_search(query_search: str, adverts: list):
    text_positions = "\n".join(f"{advert.position} - {advert.price} руб." for advert in adverts)
    text = f"Ваш запрос: <b>{query_search}</b>\n\nПозиции и цена:\n<u>{text_positions}</u>" 
    return text


async def get_adverts_by_query_search(client: httpx.AsyncClient, query: str) -> str:
    result = await client.get(
        url="https://catalog-ads.wildberries.ru/api/v5/search",
        params={"keyword": query}
    )
    try:
        result = result.json()
        positions = result["pages"][0]["positions"]
    except (KeyError, IndexError, TypeError, JSONDecodeError):
        raise BadRequestInWB
    adverts = _parse_adverts_to_positions(result, positions)
    text = _create_text_message_by_query_search(query, adverts)
    return text


async def main():
    headers = get_headers()
    async with httpx.AsyncClient(headers=headers, timeout=TIMEOUT) as client:
        a = await get_adverts_by_query_search(client, "клавиатура")
        print(a)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

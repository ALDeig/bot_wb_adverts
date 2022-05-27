import asyncio

from dataclasses import dataclass
from json.decoder import JSONDecodeError

import httpx


@dataclass
class Price:
    scu: int
    position: int
    price: int


USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
]

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    'user-agent': USER_AGENT_LIST[3]
}

PARAMS = {
    'spp': '0',
    'regions': '75,64,4,38,30,33,70,66,40,71,22,31,68,80,69,48,1',
    'stores': '119261,122252,122256,117673,122258,122259,121631,122466,122467,122495,122496,122498,122590,122591,\
122592,123816,123817,123818,123820,123821,123822,124093,124094,124095,124096,124097,124098,124099,124100,124101,124583,\
124584,125238,125239,125240,132318,132320,132321,125611,133917,132871,132870,132869,132829,133084,133618,132994,133348,\
133347,132709,132597,132807,132291,132012,126674,126676,127466,126679,126680,127014,126675,126670,126667,125186,116433,\
119400,507,3158,117501,120602,6158,121709,120762,124731,1699,130744,2737,117986,1733,686,132043',
    'pricemarginCoeff': '1.0',
    'reg': '0',
    'appType': '1',
    'offlineBonus': '0',
    'onlineBonus': '0',
    'emp': '0',
    'locale': 'ru',
    'lang': 'ru',
    'curr': 'rub',
    'couponsGeo': '12,3,18,15,21',
    'xsearch': 'true',
}

PARAMS_ADS = {
    "spp": 0,
    "regions": "68,64,83,4,38,80,33,70,82,86,75,30,69,48,22,1,66,31,40,71",
    "stores": "119261,122252,122256,117673,122258,122259,121631,122466,122467,122495,122496,122498,122590,122591,\
122592,123816,123817,123818,123820,123821,123822,124093,124094,124095,124096,124097,124098,124099,124100,124101,124583,\
124584,125238,125239,125240,132318,132320,132321,125611,133917,132871,132870,132869,132829,133084,133618,132994,133348,\
133347,132709,132597,132807,132291,132012,126674,126676,127466,126679,126680,127014,126675,126670,126667,125186,116433,\
119400,507,3158,117501,120602,6158,121709,120762,124731,1699,130744,2737,117986,1733,686,132043",
    "pricemarginCoeff": "1.0",
    "reg": 0,
    "appType": 1,
    "emp": 0,
    "locale": "ru",
    "lang": "ru",
    "curr": "rub",
    "couponsGeo": "12,3,18,15,21",
    "dest": "-1029256,-102269,-1278703,-1255563"
}

BRAND_URL = "https://wbxsearch.wildberries.ru/exactmatch/v3/common"
PARAMS_URL = "https://wbxsearch.wildberries.ru/exactmatch/v2/common"
SEARCH_URL = "https://wbxcatalog-ru.wildberries.ru/{category}/catalog"
ADS_URL = "https://catalog-ads.wildberries.ru/api/v4/search"
TIMEOUT = 20


class BadRequestInWB(Exception):
    pass


# def _parse_filters(filters: dict):
#     params = {}
#     params["ssubject"] = ",".join(str(item["id"]) for item in filters[0]["items"])
#     params["skind"] = ",".join(str(item["id"]) for item in filters[1]["items"])
#     params["scolor"] = ",".join(str(item["id"]) for item in filters[2]["items"])
#     params["brands"] = [item["id"] for item in filters[3]["items"]]
#     return params
# 
# 
# async def _get_filters(client: httpx.AsyncClient, query: str): 
#     params = {
#         "filters": "xsubject;fkind;fcolor;fbrand",
#         "spp": 0,
#         "regions": "68,64,83,4,38,80,33,70,82,86,75,30,69,48,22,1,66,31,40,71",
#         "stores": "119261,122252,122256,117673,122258,122259,121631,122466,122467,122495,122496,122498,122590,122591,\
# 122592,123816,123817,123818,123820,123821,123822,124093,124094,124095,124096,124097,124098,124099,124100,124101,124583,\
# 124584,125238,125239,125240,132318,132320,132321,125611,133917,132871,132870,132869,132829,133084,133618,132994,133348,\
# 133347,132709,132597,132807,132291,132012,126674,126676,127466,126679,126680,127014,126675,126670,126667,125186,116433,\
# 119400,507,3158,117501,120602,6158,121709,120762,124731,1699,130744,2737,117986,1733,686,132043",
#         "pricemarginCoeff": "1.0",
#         "reg": "0",
#         "appType": "1",
#         "emp": "0",
#         "locale": "ru",
#         "lang": "ru",
#         "curr": "rub",
#         "couponsGeo": "12,3,18,15,21",
#         "dest": "-1029256,-102269,-1278703,-1255563",
#         "query": query,
#         "resultset": "filters"
#     }
#     try:
#         response = await client.get(BRAND_URL, params=params, timeout=60)
#     except httpx.TimeoutException:
#         raise BadRequestInWB
# 
#     try:
#         filters = response.json()["filters"]["data"]["filters"]
#         return filters
#     except (KeyError, JSONDecodeError):
#         raise BadRequestInWB
# 
# 
# async def _get_ads(client: httpx.AsyncClient, got_params: dict, query_search: str):
#     params = PARAMS_ADS.copy()
#     brands = got_params.pop("brands")
#     params.update(got_params)
#     params["search"] = query_search
#     try:
#         response = await client.post(ADS_URL, params=params, json={"brands": brands}, timeout=60)
#         return response.json()
#     except (httpx.TimeoutException, JSONDecodeError):
#         raise BadRequestInWB
# 
# 
# def _remove_first_position(prices: list[Price]) -> list[Price]:
#     if prices[0].price < prices[1].price:
#         prices.pop(0)
#         for price in prices:
#             price.position = price.position - 1
#     return prices
# 
# 
# async def get_position_with_price(query_text: str) -> list[Price] | None:
#     async with httpx.AsyncClient(headers=HEADERS) as client:
#         filters = await _get_filters(client, query_text)
#         params = _parse_filters(filters)
#         ads = await _get_ads(client, params, query_text)
#         if not ads:
#             return 
#         prices = [Price(position=ad["position"], price=ad["cpm"], scu=ad["id"]) for ad in ads]
#         updated_prices = _remove_first_position(prices)
#         return updated_prices


async def get_adverts_by_query_search(client: httpx.AsyncClient, query: str) -> list[Price] | None:
    # async with httpx.AsyncClient(headers=HEADERS) as client:
    result = await client.get(
        url="https://catalog-ads.wildberries.ru/api/v5/search",
        params={"keyword": query}
    )
    try:
        result = result.json()
        positions = result["pages"][0]["positions"]
    except (KeyError, IndexError, JSONDecodeError):
        raise BadRequestInWB
    adverts = []
    for position in positions:
        index = position - 1 if positions[0] == 1 else position - positions[0]
        try:
            adverts.append(Price(
                scu=result["adverts"][index]["id"],
                position=position,
                price=result["adverts"][index]["cpm"]
            ))
        except IndexError:
            raise BadRequestInWB
    return adverts



if __name__ == "__main__":
    query = "шампунь"
    from pprint import pprint
    ads = asyncio.run(main(query))
    ads2 = asyncio.run(get_position_with_price(query))
    print(query + "\n\n")
    pprint(ads)
    print("*" * 100)
    pprint(ads2)


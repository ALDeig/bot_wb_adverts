import urllib.parse
from typing import NamedTuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
 

PROXY = "168.80.203.29:8000"


class Advert(NamedTuple):
    position: int
    card_id: int
    cpm: int



# options = webdriver.ChromeOptions()
# options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
# options.add_argument("--disable-blink-features=AutomationControlled")
# options.add_argument("--no-sandbox")
# options.add_argument("start-maximized")
# options.add_argument("disable-infobars")
# options.add_argument("--disable-extensions")
# options.headless = True
path_to_chromedriver = str(Path.cwd() / "chromedriver")


class SelectedCard:
    def __init__(self, query):
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server=%s" % PROXY)
        options.headless = True
        s = Service(executable_path=path_to_chromedriver)
        self.driver = webdriver.Chrome(service=s, options=options)
        self._query=urllib.parse.quote(query)

    def get_card_id_selected_card(self) -> list:
        self.driver.get(f"https://www.wildberries.ru/catalog/0/search.aspx?sort=popular&search={self._query}")
        self.driver.implicitly_wait(6)
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".advert-card-item")
        # elem = self.driver.find_element(By.CSS_SELECTOR, "button.nav-element__geo.hide-desktop.j-geocity-link.j-wba-header-item")
        # print(elem.text)
        result = []
        for card in cards:
            result.append(card.get_attribute("data-popup-nm-id"))
        self.driver.close()
        return result


class SearchEngineAdvert:
    def __init__(self, query: str, list_all_adverts: list, positions: list):
        self._list_all_adverts = list_all_adverts
        self._positions = positions
        self._query = query

    def get_adverts_card(self) ->list[Advert]:
        format_query = self._format_query(self._query)
        ads_cards = SelectedCard(format_query)
        selected_adverts_first_page = ads_cards.get_card_id_selected_card()
        result_from_first_page = self._diff_selected_adverts_with_all_adverts(
            selected_adverts=selected_adverts_first_page,
            all_adverts=self._list_all_adverts,
            positions=self._positions[0]["positions"]
        )
        return result_from_first_page
        # result_from_second_page = self._diff_selected_adverts_with_all_adverts(
        #     selected_adverts=selected_adverts_second_page,
        #     all_adverts=list_all_adverts,
        #     positions=positions[1]["positions"]
        # )
        # await self._session.close()
        # return result_from_first_page, result_from_second_page

    # async def _get_list_all_adverts(self):
    #     # headers = get_headers()
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(
    #             "https://catalog-ads.wildberries.ru/api/v5/search",
    #             # headers=headers,
    #             params={"keyword": self._query},
    #             timeout=TIMEOUT
    #         )
    #         data = response.json()
    #         return data.get("adverts"), data.get("pages")


    @staticmethod
    def _find_adverts_card_in_page(response) -> list:
        adverts = response.html.find(".advert-card-item")
        selected_adverts = []
        for advert in adverts:
            selected_adverts.append(advert.attrs.get("data-popup-nm-id"))
        return selected_adverts

    # @staticmethod
    # def _change_url_for_next_page(response):
    #     for html in response.html:
    #         url = str(html.url)
    #         split_url = url.split("?")
    #         params = "?page=2&" + split_url[1]
    #         new_url = split_url[0] + params
    #         html.url = new_url
    #     return response


 #    async def _get_selected_adverts(self) -> tuple[list, list]:
 #        params={"sort": "popular", "search": self._query}
 #        response = await self._session.get(
 #            "https://www.wildberries.ru/catalog/0/search.aspx",
 #            headers=HEADERS,
 #            params=params,
 #        )
 #        await response.html.arender(retries=5, sleep=1, keep_page=True, scrolldown=1)
 #        selected_adverts_from_first_page = self._find_adverts_card_in_page(response)
 #        return selected_adverts_from_first_page, []
        # response = self._change_url_for_next_page(response)
        # response = await self._session.get(response.html.url)
        # await response.html.arender(retries=5, sleep=1, keep_page=True, scrolldown=3)
        # selected_adverts_from_second_page = self._find_adverts_card_in_page(response)
        # return selected_adverts_from_first_page, selected_adverts_from_second_page


    def _format_query(self, query):
        return "+".join(query.split())

    @staticmethod
    def _diff_selected_adverts_with_all_adverts(
            selected_adverts: list[str],
            all_adverts: list[dict],
            positions: list) -> list[Advert]:
        result = []
        for index, position in enumerate(positions):
            for advert in all_adverts:
                try:
                    if int(selected_adverts[index]) == advert.get("id"):
                        result.append(Advert(position=position, card_id=int(selected_adverts[index]), cpm=advert["cpm"]))
                except IndexError:
                    break
        return result


def get_adverts(query: str, list_adverts: list, positions: list):
    search_engine = SearchEngineAdvert(query, list_adverts, positions)
    adverts = search_engine.get_adverts_card()
    text = f"Ваш запрос: <b>{query}</b>\n\nПозиции и цена:\n"  # <b>1-ая страница</b>\n"
    for advert in adverts:
        text += f"{advert.position} - {advert.cpm} руб.\n"  #  - Артикул: {advert.card_id}\n"
    return text
    # text += "\n<b>Вторая страница</b>\n"
    # for advert in adverts[1]:
    #     text += f"Позиция: {advert.position} - Цена: {advert.cpm} - Артикул: {advert.card_id}\n"
    # return text
    # await bot.send_message(user_id, text)

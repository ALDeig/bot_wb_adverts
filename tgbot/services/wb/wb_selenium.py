import json
import urllib.parse
from typing import NamedTuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
 

PROXY = "109.172.114.4:45785"


class Advert(NamedTuple):
    position: int
    card_id: int
    cpm: int


path_to_chromedriver = str(Path.cwd() / "chromedriver")


class SelectedCard:
    def __init__(self, query):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server=%s" % PROXY)
        options.headless = True
        s = Service(executable_path=path_to_chromedriver)
        self.driver = webdriver.Chrome(service=s, options=options)
        query = self._format_query(query)
        self._query=urllib.parse.quote(query)

    def get_cards(self) -> tuple:
        selected_card = self._get_card_id_selected_card()
        adverts, positions = self._get_all_adverts_card_with_price()
        return selected_card, adverts, positions

    def _get_card_id_selected_card(self) -> list:
        self.driver.get(f"https://www.wildberries.ru/catalog/0/search.aspx?sort=popular&search={self._query}")
        self.driver.implicitly_wait(6)
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".advert-card-item")
        # elem = self.driver.find_element(By.CSS_SELECTOR, "button.nav-element__geo.hide-desktop.j-geocity-link.j-wba-header-item")
        result = []
        for card in cards:
            result.append(card.get_attribute("data-popup-nm-id"))
        # self.driver.close()
        return result

    def _get_all_adverts_card_with_price(self) -> tuple:
        self.driver.get(f"https://catalog-ads.wildberries.ru/api/v5/search?keyword={self._query}")
        elem = self.driver.find_element(By.CSS_SELECTOR, "pre")
        page_as_json = json.loads(elem.text)
        self.driver.close()
        return page_as_json.get("adverts"), page_as_json.get("pages")

    @staticmethod
    def _format_query(query):
        return "+".join(query.split())


class SearchEngineAdvert:
    def __init__(self, selected_cards: list, list_all_adverts: list, positions: list):
        self._list_all_adverts = list_all_adverts
        self._positions = positions
        # self._query = query
        self._selected_cards = selected_cards

    def get_adverts_card(self) ->list[Advert]:
        # format_query = self._format_query(self._query)
        # ads_cards = SelectedCard(format_query)
        # selected_adverts_first_page = ads_cards.get_card_id_selected_card()
        selected_adverts_first_page = self._selected_cards
        result_from_first_page = self._diff_selected_adverts_with_all_adverts(
            selected_adverts=selected_adverts_first_page,
            all_adverts=self._list_all_adverts,
            positions=self._positions[0]["positions"]
        )
        return result_from_first_page

    @staticmethod
    def _find_adverts_card_in_page(response) -> list:
        adverts = response.html.find(".advert-card-item")
        selected_adverts = []
        for advert in adverts:
            selected_adverts.append(advert.attrs.get("data-popup-nm-id"))
        return selected_adverts

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


def get_adverts(query: str):  # , list_adverts: list, positions: list):
    # search_engine = SearchEngineAdvert(query, list_adverts, positions)
    # adverts = search_engine.get_adverts_card()
    card = SelectedCard(query)
    selected_cards, adverts, positions = card.get_cards()
    search_engine = SearchEngineAdvert(selected_cards, adverts, positions)
    adverts = search_engine.get_adverts_card()
    text = f"?????? ????????????: <b>{query}</b>\n\n?????????????? ?? ????????:\n"  # <b>1-???? ????????????????</b>\n"
    for advert in adverts:
        text += f"{advert.position} - {advert.cpm} ??????.\n"
    return text
    # text += "\n<b>???????????? ????????????????</b>\n"
    # for advert in adverts[1]:
    #     text += f"??????????????: {advert.position} - ????????: {advert.cpm} - ??????????????: {advert.card_id}\n"
    # return text
    # await bot.send_message(user_id, text)



def test_1(query: str):
    card = SelectedCard(query)
    selected_cards, adverts, positions = card.get_cards()
    search_engine = SearchEngineAdvert(selected_cards, adverts, positions)
    result = search_engine.get_adverts_card()
    print(result)



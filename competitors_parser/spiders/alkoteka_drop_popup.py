from typing import Iterator
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider

ALL_URLS = [
    'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',
]
API_URLS = (
    'https://alkoteka.com/web-api/v1/product?city_uuid='
    '4a70f9e0-46ae-11e7-83ff-00155d026416&'
    'page=1&per_page=20&'
    'root_category_slug=slaboalkogolnye-napitki-2'
)


class AlkotekaFirstSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта remex.ru."""
    name = 'alkoteka_first'
    allowed_domains = ['alkoteka.com']
    start_urls = ['https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',]

    def __init__(self):
        self.driver = webdriver.Firefox()

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг url."""
        self.driver.get(self.start_urls[0])

        try:
            time.sleep(3)
            button_18 = self.driver.find_element(
                By.XPATH, 
                '//button[text()="Мне есть 18 лет"]'
            )
            button_18.click()
            time.sleep(1)
            button_change = self.driver.find_element(
                By.XPATH,
                '//button[normalize-space()="Изменить"]'
            )
            button_change.click()
            time.sleep(1)
            self.driver.find_element(
                By.XPATH,
                '//button[text()="Краснодар"]'
            ).click()
            time.sleep(2)
            # url = self.start_urls[0]
            # yield Request(url, callback=self.parse2)
        except Exception as e:
            print(e)
        self.driver.close()
        category_name = response.xpath('//button[text()="Слабоалкогольные напитки"]')
        print(category_name)
        print(response.text)

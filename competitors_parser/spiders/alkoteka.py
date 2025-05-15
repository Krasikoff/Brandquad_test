from typing import Any, Dict, Iterator
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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


class AlkotekaSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта remex.ru."""
    name = 'alkoteka'
    allowed_domains = ['alkoteka.com']
    start_urls = ['https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',]

    def __init__(self):
        self.driver = webdriver.Firefox()

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг url."""
        self.driver.get(self.start_urls[0])
        while True:
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
                url = self.start_urls[0]
                yield Request(url, callback=self.parse2)
            except Exception as e:
#                print(e)
                break
        self.driver.close()

    def parse2(self, response):
        print(response.text)
        print(response.url)
        category_name = response.xpath('//button[text()="Слабоалкогольные напитки"]')
#        category_url = response.urls
        print(category_name)
            
            # if not category_url:
            #     continue

        # if category_name:
        #     category_name = category_name.capitalize()

        # self.logger.info(
        #     'Processing category: %s (%s)',
        #     category_name,
        #     category_url
        # )

        # yield Request(
        #     url=response.urljoin(category_url),
        #     callback=self.parse_category,
        #     cb_kwargs={'category': category_name}
        # )

    # def parse_category(
    #         self,
    #         response: Response,
    #         category: str
    #         ) -> Iterator[Request]:
    #     """Парсинг страницы категории."""
    #     products_table = response.xpath(
    #         '//*[@class="price-table price-table-images"]'
    #     )

    #     for product_link in products_table.css('a::attr(href)').getall():
    #         if not product_link:
    #             continue

    #         self.logger.info('Processing product: %s', product_link)

    #         yield Request(
    #             url=response.urljoin(product_link),
    #             callback=self.parse_product,
    #             cb_kwargs={'category': category}
    #         )

    # def parse_product(
    #         self,
    #         response: Response,
    #         category: str
    #         ) -> Iterator[Dict[str, Any]]:
    #     """Парсинг карточки товара."""
    #     product_table = response.xpath('//*[@class="price-table pprtbl"]')
    #     rows = product_table.css('tr')

    #     for row in rows:
    #         cells = row.css('td::text').getall()
    #         if len(cells) != 3:
    #             continue

    #         name, unit, price_str = [self.clean_text(cell) for cell in cells]

    #         # Валидация обязательных полей
    #         if not name or not price_str:
    #             continue

    #         try:
    #             price = self.extract_price(price_str)
    #         except ValueError:
    #             self.logger.warning(
    #                 'Invalid price format for product %s: %s',
    #                 name,
    #                 price_str
    #             )
    #             continue

    #         # Создаем структуру данных согласно ТЗ
    #         yield {
    #             'category': category,
    #             'product_code': name,
    #             'name': name,
    #             'price': price,
    #             'stocks': [{
    #                 'stock': 'Москва',
    #                 'quantity': 0,
    #                 'price': price
    #             }],
    #             'unit': unit,
    #             'currency': 'RUB',
    #             'weight': None,
    #             'length': None,
    #             'width': None,
    #             'height': None,
    #             'url': response.url,
    #         }

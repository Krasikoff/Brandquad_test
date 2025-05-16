import json
from collections import deque
from typing import Iterator, Dict, Any, List
import time
from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider

WEB_URL_CAT = 'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2'

WEB_URL_PROD = 'https://alkoteka.com/product/pivo-1/caringer-shvarc-bir_29294'

API_URL_CAT = (
    'https://alkoteka.com/web-api/v1/product?'
    'city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&'
    'page=1&per_page=20&'
    'root_category_slug=slaboalkogolnye-napitki-2'
)
API_URL_PROD = (
    'https://alkoteka.com/web-api/v1/product/'
    'caringer-shvarc-bir_29294?'
    'city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416'
)


class AlkotekaSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта remex.ru."""
    name = 'alkoteka'
    allowed_domains = ['alkoteka.com']
    start_urls = [
        'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',
        'https://alkoteka.com/catalog/krepkiy-alkogol',
    ]

    # API URL шаблоны
    BASE_URL_CAT = 'https://alkoteka.com/catalog/'
    BASE_URL_PROD = 'https://alkoteka.com/product/'
    BASE_API_URL_BEGIN = 'https://alkoteka.com/web-api/v1/product'
    # Краснодар
    BASE_API_CITY_UUID = '?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416'
    # 1стр, 20 на стр
    BASE_API_PAGE_BEGIN = '&page='
    BASE_API_PAGE_END = '&per_page=20&'
    PAGE = 1
    PAGES = {}
    BASE_API_URL_CAT = (
        f'{BASE_API_URL_BEGIN}{BASE_API_CITY_UUID}'
        f'{BASE_API_PAGE_BEGIN}{PAGE}{BASE_API_PAGE_END}'
        'root_category_slug='
    )
    BY_STOCKS = False

    # Настройки для API запросов
    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 8,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
        'DUPEFILTER_DEBUG': True
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Множество для отслеживания обработанных товаров
        self.processed_slugs = set()
        self.processed_ids = set()

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг url."""
        title = response.css('title::text').get()
        category_name = title.replace(
            'купить в г.Краснодар  по доступной цене', ''
        )
        category_list_url = [
            url.replace(
                self.BASE_URL_CAT, self.BASE_API_URL_CAT
            ) for url in self.start_urls
        ]
        for category_url in category_list_url:
            category_slug = category_url.replace(self.BASE_API_URL_CAT, '')
            self.PAGES[category_slug] = 1
            print(category_url)
            print(category_name)
            print(category_slug)

            yield Request(
                url=category_url,
                callback=self.parse_product_list,
                cb_kwargs={
                    'cat': category_name,
                    'cat_slug': category_slug,
                },
                dont_filter=True
            )

    def parse_product_list(
            self,
            response: Response,
            cat: str,
            cat_slug: str
            ) -> Iterator[Request]:
        """Парсинг списка товаров в категории."""
        try:
            result = json.loads(response.body)
            products = result.get('results', [])
            self.logger.info(f'Найдено {len(products)} товаров в {cat}')

            for product in products:
                product_slug = product.get('slug', '')
                product_title = product.get('name', '')
                if not product_slug:
                    continue

                # Проверяем, не обрабатывали ли мы уже этот товар
                if product_slug in self.processed_slugs:
                    self.logger.info(
                        f'Пропускаем дубликат товара: {product_title}'
                    )
                    continue

                # Добавляем slug в множество обработанных товаров
                self.processed_slugs.add(product_slug)

                url = (
                    f'{self.BASE_API_URL_BEGIN}/{product_slug}'
                    f'{self.BASE_API_CITY_UUID}'
                )

                yield Request(
                    url=url,
                    callback=self.parse_product,
                    cb_kwargs={
                        'cat': cat,
                        'slug': product_slug
                    },
                    dont_filter=False
                )
                time.sleep(0.3)
        except json.JSONDecodeError as e:
            self.logger.error(f'Ошибка декодирования JSON: {str(e)}')
        except Exception as e:
            self.logger.error(f'Ошибка при обработке списка товаров: {str(e)}')

        more_pages = result.get('meta', {})
        if more_pages['has_more_pages']:
            self.PAGES[cat_slug] += 1
            print(f'has_more_pages, follow next page {self.PAGES[cat_slug]}')
            next_page = (
                f'{self.BASE_API_URL_BEGIN}{self.BASE_API_CITY_UUID}'
                f'{self.BASE_API_PAGE_BEGIN}{self.PAGES[cat_slug]}'
                f'{self.BASE_API_PAGE_END}'
                f'root_category_slug={cat_slug}'
            )
            print(next_page)
            yield response.follow(
                next_page,
                callback=self.parse_product_list,
                cb_kwargs={
                    'cat': cat,
                    'cat_slug': cat_slug,
                },
            )

    def parse_product(
            self,
            response: Response,
            cat: str,
            slug: str
            ) -> Iterator[Dict[str, Any]]:
        """Парсинг данных о товаре."""
        try:
            result = json.loads(response.body)
            product = result.get('results', {})
            product_id = product['uuid']
            # print(product_id)
            product_title = product.get('name', '')
            main_price = product.get('price', '')

            # Проверяем, не обрабатывали ли мы уже этот товар
            if product_id in self.processed_ids:
                self.logger.info(
                    f'Пропускаем дубликат товара с ID: {product_id}'
                )

            # Добавляем ID в множество обработанных товаров
            self.processed_ids.add(product_id)

            subcategory = product.get('category', [])
            subcategory_slug = subcategory['slug']

            # Формирование корректного URL для товара
            product_url = f'{self.BASE_URL_PROD}{subcategory_slug}/{slug}'

            # Получаем основную единицу измерения товара
            filter_labels = product.get('filter_labels', [])
            main_unit = filter_labels[0].get('title', 'шт')

            # Получаем информацию о складах
            if self.BY_STOCKS:
                stocks = self._get_normalized_stocks(product)
            else:
                stocks = []
                amount = product.get('quantity_total', '')
                stocks.append({
                    'stock': "Краснодар (Итого)",
                    'quantity': amount,
                    'price': main_price
                })

            yield {
                'category': cat,
                'product_code': f'{product_id}',
                'name': product_title,
                'price': main_price,
                'stocks': stocks,
                'unit': main_unit,
                'currency': 'RUB',
                'url': product_url,
            }
            time.sleep(0.5)

        except json.JSONDecodeError as e:
            self.logger.error(f'Ошибка декодирования JSON: {str(e)}')
        except Exception as e:
            self.logger.error(f'Ошибка при обработке товара: {str(e)}')

    def _get_normalized_stocks(
            self,
            product: Dict[str, Any]
            ) -> List[Dict[str, Any]]:
        """
        Нормализация данных о складах с разделением по единицам измерения.
        """
        result = []

        # Обрабатываем доступные адреса
        available = product.get('availability', [])
        stores = available['stores']
        for store in stores:
            unit_title = store['title']
            amount = store['quantity']

            # Получаем цену для данной единицы измерения
            unit_price = store['price']

            # Добавляем запись для Краснодара
            result.append({
                'stock': f"Краснодар ({unit_title})",
                'quantity': amount,
                'price': unit_price
            })
        if not result:
            result.append({
                'stock': 'Нет в наличии',
                'quantity': 0,
                'price': self._get_price_for_unit(
                    product,
                    product.get('unit', 'шт')
                    )
            })

        return result

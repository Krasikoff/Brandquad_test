import copy
import json
import time
from datetime import datetime
from typing import Any, Dict, Iterator, List

from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider


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
#        more_pages = False  # TODO удалить в конечном варианте
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
            product_title = product.get('name', '')
            main_price = product.get('price', '')
            prev_price = product.get('prev_price', '')
            category = product['category']['parent']['name']
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
            # Получаем может здесь "marketing_tags"? не уверен, пока []
            # filter_labels = product.get('filter_labels', [])

            # Получаем информацию о складах
            stocks = {}
            stocks['count'] = product.get('quantity_total', '')
            if stocks['count']:
                stocks['in_stock'] = True
            else:
                stocks['count']
                stocks['in_stock'] = False
            assets = {}
            assets['main_image'] = product.get('image_url', '')
            assets['set_images'] = [assets['main_image'],]
            assets['view360'] = []
            assets['video'] = []
            now = datetime.now()
            timestamp = int(now.timestamp())
            marketing_tags = []
            price_data = self._get_prices(prev_price, main_price)
            mdata = self._get_mdata(product)
            brand = mdata.get('Бренд', '')
            yield {
                'timestamp': timestamp,
                'RPC': f'{product_id}',
                'url': product_url,
                'title': product_title,
                'marketing_tags': marketing_tags,
                'brand': brand,
                'section': category,
                'price_data': price_data,
                'stocks': stocks,
                'assets': assets,
                'metadata': mdata,
            }
            time.sleep(0.5)

        except json.JSONDecodeError as e:
            self.logger.error(f'Ошибка декодирования JSON: {str(e)}')
        except Exception as e:
            self.logger.error(f'Ошибка при обработке товара: {str(e)}')

    def _get_mdata(
        self,
        product: Dict[str, Any]
    ) -> Dict[str, Any]:
        mdata = {}
        descr_blocks = product.get('description_blocks', {})
        for item in descr_blocks:
            values = item.get('values', [])
            if len(values):
                key = copy.deepcopy(item['title'])
                value = (item['values'][0]['name'])
                mdata.update({key: value})
        text_bloks = product.get('text_blocks', {})
        for item in text_bloks:
            if item['title'] == 'Описание':
                mdata['__description'] = item['content']
            else:
                mdata[item['title']] = item['content']
        return mdata

    def _get_prices(
        self,
        original: str,
        current: str,
    ) -> List[Dict[str, Any]]:
        """current, "original, sale_tag = Скидка {discount_percentage}%"""
        result = []
        if not original:
            original = current = float(current)
            discount_percentage = ''
        elif not current:
            # original = current = float(original) # в тз нет ответа
            original = current = discount_percentage = ''
        else:
            original = float(original)
            current = float(current)
            discount_percentage = round(
                (original - current) / original * 100, 2
            )
        result.append({
            'original': original,
            'current': current,
            'discount_percentage': discount_percentage,
        })
        return result[0]

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

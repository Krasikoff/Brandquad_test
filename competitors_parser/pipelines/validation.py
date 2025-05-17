import logging
from typing import Any, Dict, List, Optional, Union

from scrapy.exceptions import DropItem


class ValidationPipeline:
    """Валидация данных перед сохранением и приведение к единому формату."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        # Обязательные поля для каждого товара согласно ТЗ
        self.required_fields = ['RPC', 'title']
        # Дополнительное обязательное поле price проверяется отдельно

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Валидация и стандартизация данных для всех пауков."""
        # Проверка обязательных полей
        for field in self.required_fields:
            if not item.get(field):
                msg = f'Missing required field: {field}'
                self.logger.warning(msg)
                raise DropItem(msg)

        # Специальная проверка поля price
        price_data = item.get('price_data')
        if price_data is None:  # Только None считается отсутствующим
            msg = 'Missing required field: price_data'
            self.logger.warning(msg)
            raise DropItem(msg)

        # Стандартизируем структуру
        normalized_item = {
            'timestamp': self._get_int_value(item, 'timestamp', ''),
            'RPC': self._get_str_value(item, 'RPC', ''),
            'url': self._get_str_value(item, 'url', ''),
            'title': self._get_str_value(item, 'title', ''),
            'brand': self._get_str_value(item, 'brand', ''),
            'section': self._get_str_value(item, 'section', ''),
            'price_data': self._normalize_price_data(item),
            'stocks': self._normalize_stocks_dict(item),
            'assets': self._normalize_assets_dict(item),
            'metadata': self._normalize_metadata_dict(item),
        }

        return normalized_item

    def _get_str_value(
            self,
            item: Dict[str, Any],
            key: str,
            default: Optional[str] = ''
            ) -> Optional[str]:
        """Получение строкового значения."""
        value = item.get(key, default)
        if value is None:
            return None
        return str(value).strip()

    def _get_float_value(
            self,
            item: Dict[str, Any],
            key: str,
            default: float = 0.0
            ) -> float:
        """Получение числового значения как float."""
        value = item.get(key, default)
        if value is None:
            return default
        try:
            # Преобразуем строку в число, заменяя запятую на точку
            if isinstance(value, str):
                value = value.replace(',', '.')
            return float(value)
        except (ValueError, TypeError):
            self.logger.warning(
                f'Invalid value for {key}: {value}, using default {default}'
                )
            return default

    def _normalize_stocks(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Нормализация данных о наличии товара на складах."""
        # Если уже в правильном формате, просто проверяем
        if 'stocks' in item and isinstance(item['stocks'], list):
            return [
                self._normalize_stock_item(stock) for stock in item['stocks']
                ]

        # Если есть поля stock и city - преобразуем в формат stocks
        if 'stock' in item or 'city' in item:
            stock_name = item.get('city', 'Основной')
            quantity = item.get('stock', 0)

            # Если quantity это строка типа "По запросу", преобразуем в 0
            if isinstance(quantity, str) and not quantity.isdigit():
                quantity = 0

            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                quantity = 0

            return [{
                'stock': stock_name,
                'quantity': quantity,
                'price': self._get_float_value(item, 'price', 0.0)
            }]

        # Если нет информации о складе, создаем пустой список
        return []

    def _normalize_stock_item(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализация отдельной записи о складе."""
        return {
            'stock': self._get_str_value(stock, 'stock', 'Основной'),
            'quantity': self._get_int_value(stock, 'quantity', 0),
            'price': self._get_float_value(stock, 'price', 0.0)
        }

    def _normalize_metadata_dict(
            self, item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Нормализация отдельной записи о складе."""
        metadata = item.get('metadata')
        if not metadata:
            return 'Validation error'
        # Если уже в виде списка, возвращаем как есть
        if isinstance(metadata, dict):
            return metadata
        # Иначе возвращаем как строку
        return str(metadata).strip()


    def _normalize_assets_dict(
            self, item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Нормализация отдельной записи о складе."""
        assets = item.get('assets')
        if not assets:
            return 'Validation error'
        # Если уже в виде списка, возвращаем как есть
        if isinstance(assets, dict):
            return assets
        # Иначе возвращаем как строку
        return str(assets).strip()

    def _normalize_price_data(
            self, item: Dict[str, Any]
    ) -> Dict[float, Any]:
        """Нормализация отдельной записи о складе."""
        price_data = item.get('price_data')
        if not price_data:
            return 'Validation error'
        # Если уже в виде списка, возвращаем как есть
        if isinstance(price_data, dict):
            return price_data
        # Иначе возвращаем как строку
        return str(price_data).strip()

    def _normalize_stocks_dict(
            self, item: Dict[int, Any]
    ) -> Dict[int, bool]:
        """Нормализация отдельной записи о складе."""
        stocks = item.get('stocks')
        if not stocks:
            return 'Validation error'
        # Если уже в виде списка, возвращаем как есть
        if isinstance(stocks, dict):
            return stocks
        # Иначе возвращаем как строку
        return str(stocks).strip()

    def _get_int_value(
            self,
            item: Dict[str, Any],
            key: str,
            default: int = 0
            ) -> int:
        """Получение числового значения как int."""
        try:
            value = item.get(key, default)
            if value is None:
                return default
            return int(float(value))
        except (ValueError, TypeError):
            self.logger.warning(
                f'Invalid value for {key}: {value}, using default {default}'
                )
            return default

    def _normalize_unit(self, item: Dict[str, Any]) -> Union[str, List[str]]:
        """Нормализация единицы измерения."""
        unit = item.get('unit')

        # Если единицы измерения нет, возвращаем значение по умолчанию
        if not unit:
            return 'шт'

        # Если единица измерения уже в виде списка, возвращаем как есть
        if isinstance(unit, list):
            return unit

        # Иначе возвращаем как строку
        return str(unit).strip()

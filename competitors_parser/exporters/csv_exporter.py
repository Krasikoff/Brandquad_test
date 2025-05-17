import csv
import json
from typing import Any, Dict

from .base import BaseExporter


class CSVExporter(BaseExporter):
    """Унифицированный CSV экспортер для всех пауков."""

    def open_spider(self, spider):
        """Инициализация экспортера при старте паука."""
        filename = self._get_filename(spider.name, 'csv')
        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')

        fieldnames = [
            'timestamp',
            'RPC',
            'url',
            'title',
            'marketing_tags',
            'brand',
            'section',
            'price_data',
            'price',
            'stocks',
            'assets',
            'metadata',
        ]

        self.exporters[spider] = csv.DictWriter(
            self.files[spider],
            fieldnames=fieldnames,
            delimiter=';'
        )
        self.exporters[spider].writeheader()
        self.logger.info(f'Начало записи в файл: {filename}')

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Обработка и запись item в CSV файл."""
        try:
            # Создаем строку для CSV
            csv_item = self._format_item(item)
            self.exporters[spider].writerow(csv_item)

        except Exception as e:
            self.logger.error(f'Ошибка при записи в CSV: {str(e)}')

        return item

    def _format_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирование item для CSV с сохранением структуры складов."""
        csv_item = {
            'timestamp': item.get('timestamp', ''),
            'RPC': item.get('RPC', ''),
            'url': item.get('url', ''),
            'title': item.get('title', ''),
            'marketing_tags': item.get('marketing_tags', ''),
            'brand': item.get('brand', ''),
            'section': item.get('section', ''),
            'price_data': item.get('price_data', ''),
            'stocks': item.get('stocks', ''),
            'assets': item.get('assets', ''),
            'metadata': item.get('metadata', ''),
        }

        stocks = item.get('stocks', {})
        if stocks:
            csv_item['stocks'] = json.dumps(stocks, ensure_ascii=False)
        else:
            csv_item['stocks'] = json.dumps([{
                'stock': 'Основной',
                'quantity': 0,
                'price': item.get('price', 0.0)
            }], ensure_ascii=False)

        return csv_item

    def _format_unit(self, unit):
        """Форматирование единицы измерения для CSV."""
        if isinstance(unit, list):
            return '; '.join(unit)
        return unit

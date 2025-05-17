import json
from collections import OrderedDict
from typing import Any, Dict

from .base import BaseExporter


class JSONExporter(BaseExporter):
    """Унифицированный JSON экспортер для всех пауков."""

    def open_spider(self, spider):
        """Инициализация экспортера при старте паука."""
        self.items = []
        self.logger.info(f'Инициализация JSON экспортера для {spider.name}')

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Обработка и сохранение item для последующей записи в JSON."""
        try:
            ordered_item = OrderedDict()
            ordered_item['timestamp'] = item.get('timestamp', '')
            ordered_item['RPC'] = item.get('RPC', '')
            ordered_item['url'] = item.get('url', '')
            ordered_item['title'] = item.get('title', '')
            ordered_item['marketing_tags'] = item.get('marketing_tags', [])
            ordered_item['brand'] = item.get('brand', '')
            ordered_item['section'] = item.get('section', '')
            ordered_item['price_data'] = item.get('price_data', [])
            ordered_item['stocks'] = item.get('stocks', {})
            ordered_item['assets'] = item.get('assets', {})
            ordered_item['metadata'] = item.get('metadata', '')

            self.items.append(ordered_item)

        except Exception as e:
            self.logger.error(f'Ошибка при обработке item для JSON: {str(e)}')

        return item

    def close_spider(self, spider):
        """Запись JSON файла при завершении работы паука."""
        try:
            filename = self._get_filename(spider.name, 'json')
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
            self.logger.info(f'Файл {filename} успешно сохранен')

        except Exception as e:
            self.logger.error(f'Ошибка при сохранении JSON: {str(e)}')

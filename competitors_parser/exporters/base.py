import logging
from datetime import datetime
from pathlib import Path


class BaseExporter:
    """Базовый класс для всех экспортеров."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.files = {}
        self.exporters = {}

    def _create_export_dir(self, spider_name: str) -> Path:
        """Создание директории для экспорта."""
        export_dir = Path(f'data/processed/{spider_name}')
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir

    def _get_filename(self, spider_name: str, extension: str) -> Path:
        """Генерация имени файла с временной меткой."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return self._create_export_dir(
            spider_name
        ) / f'{spider_name}_{timestamp}.{extension}'

    def open_spider(self, spider):
        """Метод, вызываемый при старте паука (должен быть переопределен)."""
        pass

    def process_item(self, item, spider):
        """Метод, вызываемый для каждого item (должен быть переопределен)."""
        return item

    def close_spider(self, spider):
        """Завершение работы при остановке паука."""
        if spider in self.files:
            filename = self.files[spider].name
            self.files[spider].close()
            self.logger.info(f'Файл {filename} успешно сохранен')

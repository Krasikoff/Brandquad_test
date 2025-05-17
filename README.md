# Brandquad_test
Test from Brandquad 

Решение Scrapy __ Тестовое задание.docx.pdf (в корне каталога.)

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Krasikoff/Brandquad_test
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

### Структура проекта

```
competitors_parser/
├── competitors_parser/     # Основной код
├── data/                  # Данные
│   └── exports/          # Результаты парсинга
├── logs/                 # Логи
├── requirements.txt      # Зависимости
├── README.md            
└── scrapy.cfg           # Конфигурация Scrapy
```

### Запуск парсера

```bash
# Запуск парсера 
scrapy crawl alkoteka
```
результат в json и csv файлах в каталоге .data/processed/alkoteka/
alkoteka_<data_time>.json



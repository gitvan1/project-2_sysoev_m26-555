import json
import os

from primitive_db.constants import DATA_DIR


def load_metadata(filepath: str) -> dict:
    """Загрузка данных из JSON-файла"""

    try:
        with open(filepath, 'r', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_metadata(filepath: str, data: dict) -> None:
    """Сохранение данных в JSON-файл"""

    with open(filepath, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_table_data(table_name: str) -> list[dict]:
    """Загрузка данныx таблицы из data/<table_name>.json"""

    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    try:
        with open(filepath, 'r', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    
def save_table_data(table_name: str, data: list[dict]) -> None:
    """Сохранение данных таблицы в data/<table_name>.json"""
    
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    with open(filepath, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
import json


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
import primitive_db.utils as utils

# Разрешённые типы столбцов
ALLOWED_TYPES = {"int", "str", "bool"}

def _validate_value(value, col_type: str) -> bool:
    """Проверить, что значение соответствует типу столбца."""
    if col_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if col_type == "str":
        return isinstance(value, str)
    if col_type == "bool":
        return isinstance(value, bool)
    return False

def create_table(metadata: dict, table_name: str, columns: list) -> dict:
    """Создание таблицы"""

    # Проверяем, что таблицы с таким именем ещё нет
    if table_name in metadata:
        print(f"Ошибка: таблица '{table_name}' уже существует.")
        return metadata

    # Инициализация
    final_columns = []
    col_names = set()
    user_defined_id = False

    for item in columns:
        if not isinstance(item, str) or ":" not in item:
            print(f"Ошибка: некорректный формат столбца: {item}. Ожидается 'имя:тип'.")
            return metadata
        col_name, col_type = item.split(":", 1)
        col_name = col_name.strip().lower()
        col_type = col_type.strip().lower()

        if not col_name:
            print("Ошибка: имя столбца не может быть пустым.")
            return metadata
        if col_name in col_names:
            print(f"Ошибка: столбец '{col_name}' указан дважды.")
            return metadata
        
        if col_type not in ALLOWED_TYPES:
            print(
                f"Ошибка: недопустимый тип '{col_type}' для столбца "
                f"'{col_name}'. Разрешены: {sorted(ALLOWED_TYPES)}."
            )
            return metadata
        
        # Проверка для ID
        if col_name == "id":
            if col_type != "int":
                print(
                    f"Ошибка: столбец ID должен иметь тип 'int', "
                    f"а указан '{col_type}'."
                )
                return metadata
            user_defined_id = True
        
        final_columns.append(f'{col_name}:{col_type}')
        col_names.add(col_name)
        
    if not user_defined_id:
        final_columns.insert(0, "id:int")
        col_names.add("id")

    # Обновляем metadata
    new_metadata = metadata.copy()
    new_metadata[table_name] = {"columns": final_columns}
    print(f"Таблица '{table_name}' успешно создана со столбцами: "
          f"{', '.join(final_columns)}")
    return new_metadata

def drop_table(metadata: dict, table_name: str) -> dict:
    """Удаление таблицы"""

    if table_name not in metadata:
        print(f"Ошибка: таблицы '{table_name}' не существует.")
        return metadata

    new_metadata = metadata.copy()
    del new_metadata[table_name]
    print(f"Таблица '{table_name}' успешно удалена.")
    return new_metadata

def insert(metadata: dict, table_name: str, values: dict) -> list[dict]:
    """Вставка строки в таблицу"""

    # Проверка существования таблицы
    if table_name not in metadata:
        print(f"Ошибка: таблицы '{table_name}' не существует.")
        return utils.load_table_data(table_name)

    # Проверка равенства количества переданных значений и количества столбцов 
    columns_list = metadata[table_name]["columns"]
    col_types = {}
    for item in columns_list:
        name, col_type = item.split(":", 1)
        col_types[name] = col_type
    user_col_types = {k: v for k, v in col_types.items() if k != "id"}
    if set(values.keys()) != set(user_col_types.keys()):
        print(
            f"Ошибка: ожидались столбцы {sorted(user_col_types)}, "
            f"получены {sorted(values.keys())}."
        )
        return utils.load_table_data(table_name)

    # Валидация типов данных
    for col_name in user_col_types.keys():
        if not _validate_value(values[col_name], user_col_types[col_name]):
            print(f"Ошибка: значение '{values[col_name]}' не соответствует "
                  f"типу '{user_col_types[col_name]}' для столбца '{col_name}'.")
            return utils.load_table_data(table_name)

    # Загрузка 
    data = utils.load_table_data(table_name)

    # Генерация id
    new_id = max((row.get("id", 0) for row in data), default=0) + 1
    new_row = {"id": new_id, **values}

    # Добавление
    data.append(new_row)

    return data

def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    """Выбор строк, соответствующих where_clause"""

    if where_clause is None:
        return list(table_data)
    
    result = []
    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            result.append(row)
    return result

def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    """Обновление строк, соответствующих where_clause, полями из set_clause"""
    
    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            row.update(set_clause)
    return table_data

def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    """Удаление строк, соответствующих where_clause"""

    result = []
    for row in table_data:
        if not all(row.get(k) == v for k, v in where_clause.items()):
            result.append(row)
    return result




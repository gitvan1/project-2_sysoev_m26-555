import primitive_db.utils as utils
from primitive_db.decorators import confirm_action, handle_db_errors, log_time

# Разрешённые типы столбцов
ALLOWED_TYPES = {"int", "str", "bool"}


def validate_value(value, col_type: str) -> bool:
    """Проверить, что значение соответствует типу столбца."""
    if col_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if col_type == "str":
        return isinstance(value, str)
    if col_type == "bool":
        return isinstance(value, bool)
    return False


@handle_db_errors
def create_table(metadata: dict, table_name: str, columns: list) -> dict:
    """Создание таблицы"""
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    final_columns = ["ID:int"]
    col_names = set("ID")

    for item in columns:
        if not isinstance(item, str) or ":" not in item:
            raise ValueError(f'Некорректный формат столбца: "{item}". '
                             'Ожидается "имя:тип".')
        col_name, col_type = item.split(":", 1)
        col_name = col_name.strip()
        col_type = col_type.strip().lower()

        if not col_name:
            raise ValueError("Имя столбца не может быть пустым.")
        if col_name in col_names:
            raise ValueError(f"Столбец '{col_name}' указан дважды.")
        
        if col_type not in ALLOWED_TYPES:
            raise ValueError(
                f'Недопустимый тип "{col_type}" для столбца "{col_name}". '
                f'Разрешены: {sorted(ALLOWED_TYPES)}.'
            )
        
        if col_name.lower() == "id":
            if col_type != "int":
                raise ValueError(f'Столбец ID должен иметь тип "int", '
                                 f"а указан '{col_type}'.")
            continue
        
        final_columns.append(f"{col_name}:{col_type}")
        col_names.add(col_name)

    new_metadata = metadata.copy()
    new_metadata[table_name] = {"columns": final_columns}
    print(f'Таблица "{table_name}" успешно создана со столбцами: '
          f"{', '.join(final_columns)}")
    return new_metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> dict:
    """Удаление таблицы"""
    if table_name not in metadata:
        raise KeyError(f'Таблицы "{table_name}" не существует.')

    new_metadata = metadata.copy()
    del new_metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return new_metadata


@handle_db_errors
@log_time
def insert(metadata: dict, table_name: str, values: dict) -> list[dict]:
    """Вставка строки в таблицу"""
    if table_name not in metadata:
        raise KeyError(f'Таблицы "{table_name}" не существует.')

    columns_list = metadata[table_name]["columns"]
    col_types = {}
    for item in columns_list:
        name, col_type = item.split(":", 1)
        col_types[name] = col_type
    user_col_types = {k: v for k, v in col_types.items() if k.lower() != "id"}
    
    if set(values.keys()) != set(user_col_types.keys()):
        raise ValueError(
            f"Ожидались столбцы {sorted(user_col_types)}, "
            f"получены {sorted(values.keys())}."
        )

    for col_name in user_col_types.keys():
        if not validate_value(values[col_name], user_col_types[col_name]):
            raise ValueError(
                f'Значение "{values[col_name]}" не соответствует '
                f'типу "{user_col_types[col_name]}" для столбца "{col_name}".'
            )

    data = utils.load_table_data(table_name)
    new_id = max((row.get("ID", 0) for row in data), default=0) + 1
    new_row = {"ID": new_id, **values}
    data.append(new_row)
    return data


@handle_db_errors
@log_time
def select(table_data: list[dict], where_clause: dict | None = None) -> list[dict]:
    """Выбор строк, соответствующих where_clause"""
    if where_clause is None:
        return list(table_data)
    
    result = []
    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            result.append(row)
    return result


@handle_db_errors
def update(table_data: list[dict], set_clause: dict, where_clause: dict) -> list[dict]:
    """Обновление строк, соответствующих where_clause, полями из set_clause"""
    for row in table_data:
        if all(row.get(k) == v for k, v in where_clause.items()):
            row.update(set_clause)

    
    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data: list[dict], where_clause: dict) -> list[dict]:
    """Удаление строк, соответствующих where_clause"""
    result = []
    for row in table_data:
        if not all(row.get(k) == v for k, v in where_clause.items()):
            result.append(row)
    return result
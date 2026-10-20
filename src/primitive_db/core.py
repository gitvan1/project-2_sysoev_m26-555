# Разрешённые типы столбцов
ALLOWED_TYPES = {"int", "str", "bool"}

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

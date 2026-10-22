import shlex

import prompt
from prettytable import PrettyTable

import primitive_db.core as core
import primitive_db.parser as parser
import primitive_db.utils as utils

METADATA_PATH = 'db_meta.json'

def _print_table(rows: list[dict], table_name: str, metadata: dict) -> None:
    """Вывод списка словарей в виде таблицы"""
    if not rows:
        print("Таблица пуста.")
        return

    # Получаем порядок столбцов из метаданных, если таблица существует
    col_names = []
    if table_name in metadata:
        for col in metadata[table_name]["columns"]:
            name, _ = col.split(":", 1)
            col_names.append(name)
    # else:
    #     # fallback: берём ключи из первой строки
    #     col_names = list(rows[0].keys())

    pt = PrettyTable()
    pt.field_names = col_names

    for row in rows:
        # Собираем значения в порядке col_names
        pt.add_row([row.get(f, "") for f in col_names])

    print(pt)

def run() -> None:
    """Главный цикл программы: загрузка метаданных, ввод команд, сохранение"""

    metadata = utils.load_metadata(METADATA_PATH)
    print_help()

    while True:
        user_input = prompt.string("\n>>>Введите команду: ").strip()
        try:
            args = shlex.split(user_input)
            command = args[0].lower()
        except ValueError:
            print("Ошибка разбора команды")
            continue
        except IndexError:
            print("Ошибка: команда отсутствует")
            continue

        # <command> exit
        if command == "exit":
            break
        # <command> help
        elif command == "help":
            print_help()
        # <command> create_table    
        elif command == "create_table":
            if len(args) >= 3:
                new_metadata = core.create_table(metadata, args[1], args[2:])
                if new_metadata != metadata:
                    metadata = new_metadata
                    utils.save_metadata(METADATA_PATH, metadata)
            else:
                print("Ошибка: create_table <имя_таблицы> <столбец:тип> ...")
                continue
        # <command> drop_table    
        elif command == "drop_table":
            if len(args) == 2:
                new_metadata = core.drop_table(metadata, args[1])
                if new_metadata != metadata:
                    metadata = new_metadata
                    utils.save_metadata(METADATA_PATH, metadata)
            else:
                print("Ошибка: drop_table <имя_таблицы>")
                continue        
        elif command == "list_tables":
            if not metadata:
                print("Таблиц пока нет.")
            else:
                tables = "\n- ".join(metadata.keys())
                print(f"- {tables}")
        # <command> insert into <t> values
        elif command == "insert":
            if (len(args) < 5 or args[1].lower() != "into" or 
                args[3].lower() != "values"):
                print("Ошибка: insert into <имя_таблицы> values (<v1>, <v2>, ...)")
                continue
            table_name = args[2]
            if table_name not in metadata:
                print(f"Ошибка: таблицы '{table_name}' не существует.")
                continue

            # Собираем значения из скобок: (v1, v2, ...)
            raw_str = " ".join(args[4:])
            if raw_str[0] == "(" and raw_str[-1] == ")":
                raw_str = raw_str[1:-1]
            
            # Разбиваем по запятым, убирая лишние пробелы
            raw_values = [v.strip().strip("'\"") for v in raw_str.split(",")]

            cols = metadata[table_name]["columns"]
            if len(raw_values) != len(cols) - 1:
                print(f"Ошибка: ожидалось {len(cols) - 1} значений, "
                      f"получено {len(raw_values)}.")
                continue

            schema = [c.split(":", 1) for c in cols if not c.startswith("id:")]
            values = {}
            ok = True
            for (col_name, col_type), raw in zip(schema, raw_values):
                try:
                    if col_type == "int":
                        values[col_name] = int(raw)
                    elif col_type == "bool":
                        if raw.lower() not in ("true", "false"):
                            raise ValueError
                        values[col_name] = raw.lower() == "true"
                    else:
                        values[col_name] = raw
                except ValueError:
                    print(f"Ошибка: '{raw}' не {col_type} для столбца '{col_name}'.")
                    ok = False
                    break
            if not ok:
                continue
            
            # Загружаем данные, вызываем core.insert, сохраняем
            old_rows = utils.load_table_data(table_name)
            new_rows = core.insert(metadata, table_name, values)
            if len(new_rows) > len(old_rows):
                utils.save_table_data(table_name, new_rows)
                new_id = new_rows[-1]["id"] 
                print(f'Запись с id={new_id} успешно добавлена в таблицу '
                      f'"{table_name}".')
            else:
                print("Не удалось добавить запись.")

        # <command> select from
        elif command == "select":
            if len(args) < 3:
                print("Ошибка: select from <имя> [where <условие>]")
                continue
            table_name = args[2]
            if table_name not in metadata:
                print(f"Ошибка: таблицы '{table_name}' не существует.")
                continue

            try:
                clauses = parser.parse_clauses(args[3:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            where = clauses["where"]
            rows = utils.load_table_data(table_name)
            result = core.select(rows, where if where else None)
            _print_table(result, table_name, metadata)

        # <command> update <t> set ... [where ...]
        elif command == "update":
            if len(args) < 4:
                print("Ошибка: update <имя> set <столбец> = <значение> "
                      "[where <условие>]")
                continue
            table_name = args[1]
            if table_name not in metadata:
                print(f"Ошибка: таблицы '{table_name}' не существует.")
                continue

            try:
                clauses = parser.parse_clauses(args[2:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            set_clause = clauses["set"]
            where_clause = clauses["where"]
            if not set_clause:
                print("Ошибка: update требует set")
                continue

            rows = utils.load_table_data(table_name)
            # Запоминаем id строк, которые подходят под условие
            target_ids = [r["id"] for r in rows if all(r.get(k) == v for k, v 
                                                       in where_clause.items())]
            updated_rows = core.update(rows, set_clause, where_clause)
            utils.save_table_data(table_name, updated_rows)
            for id_ in target_ids:
                print(f'Запись с id={id_} в таблице "{table_name}" успешно обновлена.')

        # <command> delete from <t> where ...
        elif command == "delete":
            if len(args) < 5 or args[1].lower() != "from" or args[3].lower() != "where":
                print("Ошибка: delete from <имя> where <условие>")
                continue
            table_name = args[2]
            if table_name not in metadata:
                print(f"Ошибка: таблицы '{table_name}' не существует.")
                continue

            try:
                clauses = parser.parse_clauses(args[3:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            where_clause = clauses["where"]
            rows = utils.load_table_data(table_name)
            # Запоминаем id строк, которые будут удалены
            target_ids = [r["id"] for r in rows if all(r.get(k) == v for k, v 
                                                       in where_clause.items())]     
            remaining_rows = core.delete(rows, where_clause)
            utils.save_table_data(table_name, remaining_rows)
            for id_ in target_ids:
                print(f'Запись с id={id_} успешно удалена из таблицы "{table_name}".')
        
        # <command> info
        elif command == "info":
            if len(args) != 2:
                print("Ошибка: info <имя_таблицы>")
                continue
            table_name = args[1]
            if table_name not in metadata:
                print(f"Ошибка: таблицы '{table_name}' не существует.")
                continue

            # Достаем данные о столбцах из метаданных
            columns_list = metadata[table_name]["columns"]
            
            # Загружаем данные, чтобы узнать количество записей
            rows = utils.load_table_data(table_name)
            
            print(f"Таблица: {table_name}")
            print(f"Столбцы: {', '.join(columns_list)}")
            print(f"Количество записей: {len(rows)}")

        else:
            print(f'Функции {command} нет. Попробуйте снова.')
            continue


def print_help() -> None:
    """Prints the help message for the current mode."""

    print("\n*** Процесс работы с таблицей ***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец:тип> .. - создать таблицу.")
    print("<command> list_tables - показать список всех таблиц.")
    print("<command> drop_table <имя_таблицы> - удалить таблицу.")
    
    print("\n*** Операции с данными ***")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы.")
    print("<command> help - справочная информация\n")


"""Запуск, игровой цикл и парсинг команд."""

import os
import shlex

import prompt
from prettytable import PrettyTable

import primitive_db.core as core
import primitive_db.parser as parser
import primitive_db.utils as utils
from primitive_db.constants import DATA_DIR, METADATA_PATH
from primitive_db.decorators import create_cacher


def _print_table(rows: list[dict], table_name: str, metadata: dict) -> None:
    """Вывод списка словарей в виде таблицы"""
    if not rows:
        print("Таблица пуста.")
        return

    col_names = []
    if table_name in metadata:
        for col in metadata[table_name]["columns"]:
            name, _ = col.split(":", 1)
            col_names.append(name)
    else:
        print("Таблица не найдена.")
        return

    pt = PrettyTable()
    pt.field_names = col_names
    for row in rows:
        pt.add_row([row.get(f, "") for f in col_names])
    print(pt)


def run() -> None:
    """Главный цикл программы: загрузка метаданных, ввод команд, сохранение"""
    metadata = utils.load_metadata(METADATA_PATH)
    cache_result = create_cacher()
    print_help()

    while True:
        try:
            user_input = prompt.string("\n>>>Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break

        if not user_input:
            continue

        try:
            args = shlex.split(user_input)
        except ValueError as e:
            print(f"Ошибка разбора команды: {e}")
            continue

        if not args:
            continue

        command = args[0].lower()

        # <command> exit
        if command == "exit":
            print("Выход из программы.")
            break

        # <command> help
        elif command == "help":
            print_help()

        # <command> create_table
        elif command == "create_table":
            if len(args) < 3:
                print("Ошибка: create_table <имя_таблицы> <столбец:тип> ...")
                continue
            new_metadata = core.create_table(metadata, args[1], args[2:])
            if new_metadata is not None:
                metadata = new_metadata
                utils.save_metadata(METADATA_PATH, metadata)

        # <command> drop_table
        elif command == "drop_table":
            if len(args) != 2:
                print("Ошибка: drop_table <имя_таблицы>")
                continue
            new_metadata = core.drop_table(metadata, args[1])
            if new_metadata is not None:
                metadata = new_metadata
                utils.save_metadata(METADATA_PATH, metadata)
                filepath = os.path.join(DATA_DIR, f"{args[1]}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                cache_result = create_cacher()

        # <command> list_tables
        elif command == "list_tables":
            if not metadata:
                print("Таблиц пока нет.")
            else:
                tables = "\n- ".join(metadata.keys())
                print(f"- {tables}")

        # <command> insert into <t> values
        elif command == "insert":
            if (len(args) < 5 or args[1].lower() != "into"
                    or args[3].lower() != "values"):
                print("Ошибка: insert into <имя_таблицы> values (<v1>, <v2>, ...)")
                continue

            table_name = args[2]
            if table_name not in metadata:
                print(f'Ошибка: таблицы "{table_name}" не существует.')
                continue

            raw_str = " ".join(args[4:]).strip()
            if raw_str.startswith("(") and raw_str.endswith(")"):
                raw_str = raw_str[1:-1]

            raw_values = [v.strip().strip("'\"") for v in raw_str.split(",")]

            cols = metadata[table_name]["columns"]
            if len(raw_values) != len(cols) - 1:
                print(f"Ошибка: ожидалось {len(cols) - 1} значений, "
                      f"получено {len(raw_values)}.")
                continue

            schema = [c.split(":", 1) for c in cols if (c[:3].lower() != "id:")]
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
                    print(f'Ошибка: "{raw}" не {col_type} для столбца "{col_name}".')
                    ok = False
                    break
            if not ok:
                continue

            old_rows = utils.load_table_data(table_name)
            new_rows = core.insert(metadata, table_name, values)
            if new_rows is not None and len(new_rows) > len(old_rows):
                utils.save_table_data(table_name, new_rows)
                new_id = new_rows[-1]["ID"]
                print(f'Запись с ID={new_id} успешно добавлена в таблицу '
                      f'"{table_name}".')
                cache_result = create_cacher()

        # <command> select from
        elif command == "select":
            if len(args) < 3:
                print("Ошибка: select from <имя> [where <условие>]")
                continue
            table_name = args[2]
            if table_name not in metadata:
                print(f'Ошибка: таблицы "{table_name}" не существует.')
                continue

            try:
                clauses = parser.parse_clauses(args[3:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            where_clause = clauses["where"]
            key = (table_name, frozenset(where_clause.items()))
            
            def _do_select():
                rows = utils.load_table_data(table_name)
                return core.select(rows, where_clause if where_clause else None)

            result = cache_result(key, _do_select)
            if result is not None:
                _print_table(result, table_name, metadata)

        # <command> update <t> set ... where ...
        elif command == "update":
            if len(args) < 5 or args[2].lower() != "set":
                print("Ошибка: update <имя> set <столбец> = <значение> "
                      "where <условие>")
                continue
            table_name = args[1]
            if table_name not in metadata:
                print(f'Ошибка: таблицы "{table_name}" не существует.')
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
            if not where_clause:
                print("Ошибка: update требует where")
                continue

            cols = metadata[table_name]["columns"]
            schema = {}
            flag_type = True
            for item in cols:
                name, col_type = item.split(":", 1)
                schema[name] = col_type

            # Проверяем, что все столбцы из set существуют
            unknown_set = set(set_clause) - set(schema)
            if unknown_set:
                print(f"Ошибка: неизвестные столбцы в set: {sorted(unknown_set)}")
                continue

            # Проверяем, что все столбцы из where существуют
            unknown_where = set(where_clause) - set(schema)
            if unknown_where:
                print(f"Ошибка: неизвестные столбцы в where: {sorted(unknown_where)}")
                continue
            
            # Запрещаем изменять ID
            if any(col.lower() == "id" for col in set_clause):
                print("Ошибка: столбец ID нельзя изменять.")
                continue

            # Проверяем типы
            for name, col_type in schema.items():
                if name in set_clause:
                    if not core.validate_value(set_clause[name], col_type):
                        print(f'Значение "{set_clause[name]}" не соответствует '
                              f'типу "{col_type}" для столбца "{name}".')
                        flag_type = False
                        break
                if name in where_clause:
                    if not core.validate_value(where_clause[name], col_type):
                        print(f'Значение "{where_clause[name]}" не соответствует '
                              f'типу "{col_type}" для столбца "{name}".')
                        flag_type = False
                        break
            if not flag_type:
                continue

            # Выполнение 
            rows = utils.load_table_data(table_name)
            target_ids = [r["ID"] for r in rows if all(r.get(k) == v for k, v
                                                       in where_clause.items())]
            updated_rows = core.update(rows, set_clause, where_clause)
            if updated_rows is not None:
                utils.save_table_data(table_name, updated_rows)
                for tid in target_ids:
                    print(f'Запись с ID={tid} в таблице "{table_name}" '
                          'успешно обновлена.')
                cache_result = create_cacher()

        # <command> delete from <t> where ...
        elif command == "delete":
            if (len(args) < 5 or args[1].lower() != "from"
                    or args[3].lower() != "where"):
                print("Ошибка: delete from <имя> where <условие>")
                continue
            table_name = args[2]
            if table_name not in metadata:
                print(f'Ошибка: таблицы "{table_name}" не существует.')
                continue

            try:
                clauses = parser.parse_clauses(args[3:])
            except ValueError as e:
                print(f"Ошибка: {e}")
                continue

            where_clause = clauses["where"]
            rows = utils.load_table_data(table_name)
            target_ids = [r["ID"] for r in rows if all(r.get(k) == v for k, v
                                                       in where_clause.items())]
            remaining_rows = core.delete(rows, where_clause)
            if remaining_rows is not None:
                utils.save_table_data(table_name, remaining_rows)
                for id_ in target_ids:
                    print(f'Запись с ID={id_} успешно удалена из '
                          f'таблицы "{table_name}".')
                cache_result = create_cacher()

        # <command> info
        elif command == "info":
            if len(args) != 2:
                print("Ошибка: info <имя_таблицы>")
                continue
            table_name = args[1]
            if table_name not in metadata:
                print(f'Ошибка: таблицы "{table_name}" не существует.')
                continue

            columns_list = metadata[table_name]["columns"]
            rows = utils.load_table_data(table_name)

            print(f"Таблица: {table_name}")
            print(f"Столбцы: {', '.join(columns_list)}")
            print(f"Количество записей: {len(rows)}")

        else:
            print(f'Функции {command} нет. Попробуйте снова.')


def print_help() -> None:
    """Вывод справки по командам."""
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

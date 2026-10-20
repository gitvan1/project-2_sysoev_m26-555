import shlex

import prompt

import primitive_db.core as core
import primitive_db.utils as utils

METADATA_PATH = 'db_meta.json'

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

        if command == "exit":
            break
        elif command == "help":
            print_help()
        elif command == "create_table":
            if len(args) >= 3:
                new_metadata = core.create_table(metadata, args[1], args[2:])
                if new_metadata != metadata:
                    metadata = new_metadata
                    utils.save_metadata(METADATA_PATH, metadata)
            else:
                print("Ошибка: create_table <имя_таблицы> <столбец:тип> ...")
                continue
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
        else:
            print(f'Функции {command} нет. Попробуйте снова.')
            continue


def print_help() -> None:
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


import time
from functools import wraps

import prompt


def handle_db_errors(func):
    """Декоратор для перехвата типичных ошибок при работе с БД.

    Перехватывает KeyError, ValueError и FileNotFoundError,
    выводит сообщение об ошибке и возвращает None.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база данных "
                  "не инициализирована.")
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
    return wrapper

def confirm_action(action_name: str):
    """Декоратор, запрашивающий подтверждение перед опасной операцией.

    :param action_name: название операции.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            answer = prompt.string(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            ).strip().lower()

            if answer != "y":
                print("Операция отменена.")
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator

def log_time(func):
    """Декоратор, замеряющий время выполнения функции.

    Выводит: Функция <имя> выполнилась за X.XXX секунд.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            func_time = time.monotonic() - start
            print(f"Функция {func.__name__} выполнилась за {func_time:.3f} секунд.")

    return wrapper

def create_cacher():
    """Создает функцию кэширования с замыканием"""

    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result
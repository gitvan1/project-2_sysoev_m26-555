# project-2_sysoev_m26-555

## Управление таблицами

После запуска `database` открывается интерактивная оболочка.

| Команда | Описание |
|---------|----------|
| `create_table <имя> <столбец:тип> ...` | Создать таблицу. `ID:int` добавляется автоматически. |
| `list_tables` | Показать список таблиц. |
| `drop_table <имя>` | Удалить таблицу. |
| `help` | Справка. |
| `exit` | Выход. |

**Допустимые типы:** `int`, `str`, `bool`.

### Пример

```text
>>> create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool

>>> list_tables
- users

>>> drop_table users
Таблица "users" успешно удалена.
```

### Демонстрация

[![asciicast](https://asciinema.org/a/iNMc75SN8BwCWmMN.svg)](https://asciinema.org/a/iNMc75SN8BwCWmMN)
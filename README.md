# project-2_sysoev_m26-555

## Управление таблицами

После запуска `database` открывается интерактивная оболочка.

| Команда | Описание |
|---------|----------|
| `create_table <имя> <столбец:тип> ...` | Создать таблицу. `id:int` добавляется автоматически. |
| `list_tables` | Показать список таблиц. |
| `drop_table <имя>` | Удалить таблицу. |
| `help` | Справка. |
| `exit` | Выход. |

**Допустимые типы:** `int`, `str`, `bool`.

### Пример

```text
>>> create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: id:int, name:str, age:int, is_active:bool

>>> list_tables
- users

>>> drop_table users
Таблица "users" успешно удалена.
```

### Демонстрация

https://asciinema.org/a/iNMc75SN8BwCWmMN

## CRUD-операции

| Команда | Описание |
|---------|----------|
| `insert into <имя> values (<знач1>, <знач2>, ...)` | Создать новую запись в таблице. |
| `select from <имя>` | Прочитать все записи из таблицы. |
| `select from <имя> where <столбец> = <значение>` | Прочитать записи, соответствующие условию. |
| `update <имя> set <столбец> = <значение> where <условие>` | Обновить записи, соответствующие условию. |
| `delete from <имя> where <столбец> = <значение>` | Удалить записи, соответствующие условию. |
| `info <имя>` | Показать структуру таблицы и количество записей. |

### Пример работы

```text
>>> create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: id:int, name:str, age:int, is_active:bool

>>> insert into users values ("Sergei", 28, true)
Запись с id=1 успешно добавлена в таблицу "users".

>>> select from users
+----+--------+-----+-----------+
| id |  name  | age | is_active |
+----+--------+-----+-----------+
| 1  | Sergei | 28  |    True   |
+----+--------+-----+-----------+

>>> update users set age = 29 where name = "Sergei"
Запись с id=1 в таблице "users" успешно обновлена.

>>> delete from users where ID = 1
Запись с id=1 успешно удалена из таблицы "users".
```

### Демонстрация

https://asciinema.org/a/9wlIb3uX6RmeNTlN
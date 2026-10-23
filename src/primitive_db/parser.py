"""Парсеры для разбора сложных аргументов команд (where и set)."""

def _parse_value(raw: str):
    """Преобразует сырую строку в Python-значение"""

    raw = raw.strip()
    # Строка в кавычках
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
        return raw[1:-1]

    # Boolean
    low = raw.lower()
    if low == "true":
        return True
    if low == "false":
        return False

    # Числа
    try:
        return int(raw)
    except ValueError:
        pass

    # Если ничего не подошло 
    return raw

def _parse_condition(condition: str) -> dict:
    """Разбирает одно условие вида 'age = 28'"""

    if "=" not in condition:
        raise ValueError(f"Некорректное условие (нет '='): '{condition}'")

    key, raw_value = condition.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Пустое имя поля в условии: '{condition}'")

    value = _parse_value(raw_value)
    return {key: value}

def _normalize_tokens(tokens: list[str]) -> list[str]:
    """Склеивает 'key', '=', 'value' в 'key=value'."""
    result = []
    i = 0
    while i < len(tokens):
        # Если текущий — имя, следующий — '=', третий — значение
        if i + 2 < len(tokens) and tokens[i + 1] == "=":
            result.append(f"{tokens[i]}={tokens[i + 2]}")
            i += 3
        else:
            result.append(tokens[i])
            i += 1
    return result

def parse_clauses(args: list[str]) -> dict[str, dict]:
    """Разбор аргументов команды на where и set"""

    args = _normalize_tokens(args)

    mode = None
    result = {"set": {}, "where": {}}

    for arg in args:
        if arg.lower() in ("set", "where"):
            mode = arg.lower()
        elif mode is not None:
            result[mode].update(_parse_condition(arg))
    return result

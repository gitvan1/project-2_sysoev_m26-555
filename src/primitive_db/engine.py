import prompt


def welcome() -> None:
    """Приветствие, подсказка и игровой цикл."""
    print("Первая попытка запустить проект!")
    print()
    print("***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")

    while True:
        command = prompt.string("Введите команду: ").strip().lower()

        if command == "exit":
            break
        elif command == "help":
            print()
            print("<command> exit - выйти из программы")
            print("<command> help - справочная информация")
        else:
            print(f"Неизвестная команда: {command!r}")
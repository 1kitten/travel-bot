import sqlite3 as sq
from typing import List, Tuple


with sq.connect('travel.db') as con:
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        user_command TEXT NOT NULL,
        request_date DATE NOT NULL,
        result TEXT NOT NULL
    )""")


def add_new_value(user_id: int, user_command: str, request_date: str, search_result: str) -> None:
    """
    Функция которая добавляет новое значение в таблицу БД.
    :param user_id: id пользователя.
    :param user_command: команда которую ввёл пользователь.
    :param request_date: дата ввода команды.
    :param search_result: результат вывода.
    """
    with sq.connect('travel.db') as con:
        cur = con.cursor()

        cur.execute(f"INSERT INTO users (user_id, user_command, request_date, result) VALUES("
                    f"{user_id},"
                    f"'{user_command}',"
                    f"'{request_date}',"
                    f"'{search_result}')")


def check_data(user_id: int) -> bool:
    """
    Функция, которая проверяет, есть ли в базе данных информация о пользователе.
    :param user_id: (str) id пользователя
    :return: bool
    """
    with sq.connect('travel.db') as con:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM users where user_id = {user_id}")
        if len(cur.fetchall()) < 1:
            return False
        return True


def show_history(user_id: int) -> List[Tuple[str]]:
    """
    Функция, которая возвращает историю поиска пользователя.
    :param user_id: (str) id пользователя.
    :return: result (List) список состоящий из кортежей в которых лежит информация
    о команде, которую ввел пользователь, дате ввода команды и результате.
    """
    with sq.connect('travel.db') as con:
        cur = con.cursor()

        cur.execute(f"""SELECT user_command, request_date, result FROM users"
                    f"WHERE user_id = {user_id} ORDER BY request_date DESC LIMIT 5""")
        result = cur.fetchall()
        return result

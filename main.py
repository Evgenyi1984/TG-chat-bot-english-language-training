from dotenv import load_dotenv

load_dotenv()

from db import open_db, close_db
from bot import run_bot


def main():
    print("Подключаемся к базе ...")
    open_db()

    print("Запускаем бот ...")
    run_bot()


if __name__ == "__main__":
    try:
        main()
    finally:
        close_db()
        print("Завершение работы")

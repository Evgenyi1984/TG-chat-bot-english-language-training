from bot import run_bot
from db import open_db, close_db, Settings
import logging


def setup_logging():
    if not Settings.LOG_FILE:
        return  # не используем лог, если не указано имя файла
    handlers = [logging.FileHandler(Settings.LOG_FILE, encoding="utf-8")]
    if Settings.LOG_TO_CONSOLE:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=Settings.LOG_LEVEL or logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def main():
    setup_logging()

    print("Подключаемся к базе ...")
    open_db()

    print("Запускаем бот и ждём сообщения ...")
    run_bot()


if __name__ == "__main__":
    try:
        main()
    finally:
        close_db()
        print("Завершение работы")

import telebot
from telebot.types import Message, User, Chat
from os import getenv
from dataclasses import dataclass, field
import json
from typing import List
from random import shuffle, choice, sample
import db
import dict



class Settings:

    def _load_setting(name, mandatory=True):
        value = getenv(name)
        if mandatory and not value:
            raise ValueError(f"Setting '{name}' is missing!")
        return value

    TOKEN = _load_setting("eng_lish_card_bot")

 


class ChatStates:
    NEW = "new"
    TRAIN = "train"
    ADD_WORD = "add"
    DELETE_WORD = "delete"
    SKIP_WORD = "skip"


class Buttons:
    ADD = "Добавить ➕️"
    DELETE = "Удалить ❌"
    SKIP = "Пропустить ⏭️"


@dataclass
class ChatState:
    cid: int
    current: str
    message: Message = field(repr=False)
    user: User = field(repr=False)
    chat: Chat = field(repr=False)
    current_word: str = None
    word_options: List[str] = field(default_factory=list)
    correct_option: str = None


bot = None
chat_state = None
known_chats = {}


def run_bot():
    global bot
    bot = telebot.TeleBot(Settings.TOKEN)

    @bot.message_handler(commands=["start"])
    def start_new_chat(message):
        send_welcome()
        send_new_word()

    @bot.message_handler()
    def message_handler(message: Message):
        print_message(message)
        if (
            get_chat_state(message) == ChatStates.NEW
            or message.text.lower() == "/start"
        ):
            send_welcome()
            send_new_word()
        else:
            match chat_state.current:
                case ChatStates.TRAIN:
                    # assume attempt to guess a word
                    user_option = message.text.lower()
                    if user_option == chat_state.correct_option:
                        correct_guess()
                    else:
                        wrong_guess()
                case ChatStates.ADD_WORD:
                    if message.text == Buttons.ADD:
                        # the add button was pressed
                        send_message(
                            "Введите слово, которое хотите добавить, - на русскои или английском"
                        )
                    else:
                        # the user entered a new word
                        add_word(message.text)
                        send_new_word()
                case ChatStates.DELETE_WORD:
                    delete_word(chat_state.current_word)
                case ChatStates.SKIP_WORD:
                    send_message("Перейдем к следующему слову")
                    send_new_word()
                case _:
                    # state not catched elsewhere
                    # assume it's a new user
                    start_new_chat()

    bot.infinity_polling()


def print_message(message: Message):
    pretty_json = json.dumps(message.json, indent=4)
    print(
        f"""
Message received: {type(message)} {message.content_type}
    User id:    {message.from_user.id}  {message.from_user.username}
    Chat:       {message.chat.id}  {message.chat.type}
    Text:       {message.text}
    JSON:       
{pretty_json}
"""
    )


def get_chat_state(message: Message):
    global chat_state
    cid = message.chat.id
    if cid in known_chats:
        chat_state = known_chats[cid]
        chat_state.message = message
        match message.text:
            case Buttons.ADD:
                set_chat_state(ChatStates.ADD_WORD)
            case Buttons.DELETE:
                set_chat_state(ChatStates.DELETE_WORD)
            case Buttons.SKIP:
                set_chat_state(ChatStates.SKIP_WORD)
        print("Chat state found", cid, chat_state.current)
    else:
        chat_state = ChatState(
            cid=cid,
            current=ChatStates.NEW,
            message=message,
            user=message.from_user,
            chat=message.chat,
        )
        known_chats[cid] = chat_state
        print("Chat state added", cid, chat_state.current)
    print(chat_state)
    return chat_state.current


def set_chat_state(new_state):
    chat_state.current = new_state
    print("Chat state updated")
    print(chat_state)


def send_message(*args, **kwargs):
    bot.send_message(chat_state.cid, *args, **kwargs)


def send_welcome():
    user_greeting = (
        " " + chat_state.user.first_name if chat_state.user.first_name else ""
    )
    welcome_message = f"""Привет{user_greeting}! 👋 

Давай попрактикуемся в английском языке. Можешь отвечать в удобном для себя темпе.

Можешь добавлять и удалять слова. Для этого воспользуйся кнопками "{Buttons.ADD}" или "{Buttons.DELETE}".

Ну что, начнём? ⬇️"""
    send_message(welcome_message)


def send_new_word():
    while True:
        # avoid repeating the same word
        russian_word, translation_options, english_word = get_word()
        if russian_word != chat_state.current_word:
            break

    chat_state.current_word, chat_state.word_options, chat_state.correct_option = (
        russian_word,
        translation_options,
        english_word,
    )

    word_message = f"Выбери перевод слова:\n\n➡️ {chat_state.current_word}"

    usage_examples = dict.fetch_examples(chat_state.correct_option)
    if usage_examples:
        examples = '\n\n'.join(usage_examples[:2])
        word_message += f'''

Примеры использования слова:

{examples}'''

    shuffle(chat_state.word_options)
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    markup.add(*chat_state.word_options + [Buttons.SKIP, Buttons.ADD, Buttons.DELETE])
    send_message(word_message, reply_markup=markup)
    set_chat_state(ChatStates.TRAIN)


def get_word():
    user_dict = db.get_user_dictionary(chat_state.user.id)
    options = sample(user_dict, k=4)
    english_word, russian_word = choice(options)
    return (russian_word, [x[0] for x in options], english_word)


def correct_guess():
    send_message("Отлично! Продолжаем")
    send_new_word()


def wrong_guess():
    send_message("Неверно! Попробуй снова")


def delete_word(word):
    word_count, _, label = get_word_count()
    if word_count < 5:
        message = f"Не могу удалить, так как в базе всего {label}."
    else:
        db.delete_user_word(chat_state.user.id, chat_state.correct_option)
        label = pluralize_word(word_count - 1)[2]
        message = f"Слово '{word}' удалено. Осталось {label}."
    send_message(f"""{message} Продолжаем?""")
    send_new_word()


def add_word(word):
    is_russian = any("а" <= char <= "я" for char in word.lower())
    translation = dict.translate(word, is_russian)
    if not translation:
        send_message(f"Перевод слова '{word}' не найден в словаре. Не могу добавить. Возвращаюсь к тренировке.")
        return
    if is_russian:
        db.add_user_word(chat_state.user.id, translation, word)
    else:
        db.add_user_word(chat_state.user.id, word, translation)
    send_message(
        f"""Слово '{word}' добавлено в базу
Перевод: '{translation}'
Всего в базе: {get_word_count()[2]}
Продолжаем!"""
    )


def get_word_count():
    word_count = len(db.get_user_dictionary(chat_state.user.id))
    return pluralize_word(word_count)


def pluralize_word(n):
    if 11 <= n % 100 <= 19:
        label = "слов"
    elif n % 10 == 1:
        label = "слово"
    elif 2 <= n % 10 <= 4:
        label = "слова"
    else:
        label = f"слов"
    return n, label, f"{n} {label}"

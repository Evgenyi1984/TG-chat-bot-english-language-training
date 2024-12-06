from os import getenv
from psycopg2 import connect


class Settings:

    def _load_setting(name, mandatory=True):
        value = getenv(name)
        if mandatory and not value:
            raise ValueError(f"Setting '{name}' is missing!")
        return value

    POSTGRES_SERVER = _load_setting("postgres_server")
    POSTGRES_DBNAME = _load_setting("postgres_dbname")
    POSTGRES_USER = _load_setting("postgres_user")
    POSTGRES_PASS = _load_setting("postgres_pass")


conn = None


def open_db():
    global conn
    conn = connect(
        host=Settings.POSTGRES_SERVER,
        database=Settings.POSTGRES_DBNAME,
        user=Settings.POSTGRES_USER,
        password=Settings.POSTGRES_PASS,
    )
    create_schema()


def create_schema():
    with conn.cursor() as cur:
        # cur.execute("""
        # DROP TABLE if exists ;
        # """)
        # conn.commit()

        cur.execute(
            """
CREATE TABLE IF NOT EXISTS bot_common_words (
    english_word varchar(50) NOT NULL,
    russian_word varchar(50) NOT NULL,
    PRIMARY KEY (english_word),
    UNIQUE (russian_word)
);

CREATE TABLE IF NOT EXISTS bot_user_words (
    uid INTEGER NOT NULL,
    english_word varchar(50) NOT NULL,
    russian_word varchar(50) NOT NULL,
    PRIMARY KEY (uid, english_word)
);

CREATE TABLE IF NOT EXISTS bot_excluded_words (
    uid INTEGER NOT NULL,
    english_word varchar(50) NOT NULL,
    PRIMARY KEY (uid, english_word),
    FOREIGN KEY (english_word) REFERENCES bot_common_words(english_word)
        ON DELETE CASCADE
);

INSERT INTO
    bot_common_words (
        english_word,
        russian_word
    )
VALUES 
    ('apple', 'яблоко'),
    ('book', 'книга'),
    ('cat', 'кот'),
    ('dog', 'собака'),
    ('egg', 'яйцо'),
    ('fish', 'рыба'),
    ('house', 'дом'),
    ('tree', 'дерево'),
    ('sun', 'солнце'),
    ('moon', 'луна'),
    ('car', 'машина'),
    ('pen', 'ручка'),
    ('chair', 'стул'),
    ('water', 'вода'),
    ('milk', 'молоко'),
    ('bird', 'птица'),
    ('table', 'стол'),
    ('ball', 'мяч'),
    ('hand', 'рука'),
    ('window', 'окно')
ON CONFLICT DO NOTHING;
"""
        )
        conn.commit()


def close_db():
    conn.close()


def get_user_dictionary(uid):
    with conn.cursor() as cur:
        cur.execute(
            """
SELECT english_word, russian_word
FROM bot_common_words
WHERE english_word NOT IN (
    SELECT english_word
    FROM bot_excluded_words
    WHERE uid = %s
)

UNION

SELECT english_word, russian_word
FROM bot_user_words
WHERE uid = %s;
""",
            (uid, uid),
        )
        all_records = cur.fetchall()
        print(f"\n{len(all_records)} words retreived for user {uid}\n")
        return all_records


def delete_user_word(uid, word):
    with conn.cursor() as cur:
        # Try to delete the word from the user's personal words
        cur.execute(
            """
DELETE FROM bot_user_words
WHERE uid = %s AND english_word = %s;
            """,
            (uid, word),
        )

        # If the word was not found in bot_user_words
        if cur.rowcount < 1:
            # Insert the word into bot_excluded_words to exclude it for this user
            cur.execute(
                """
INSERT INTO bot_excluded_words (uid, english_word)
VALUES (%s, %s)
ON CONFLICT DO NOTHING;
                """,
                (uid, word),
            )

        # Commit the changes
        conn.commit()


def add_user_word(uid, word, translation):
    with conn.cursor() as cur:
        cur.execute(
            """
INSERT INTO
    bot_user_words (
        uid,
        english_word,
        russian_word
    )
VALUES 
    (%s, %s, %s)
ON CONFLICT DO NOTHING;""",
            (uid, word, translation),
        )
        conn.commit()

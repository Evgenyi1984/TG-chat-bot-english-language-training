# =================================================================
# fetching usage examples from dictionaryapi
# =================================================================

import requests


API_ADDRESS = "https://api.dictionaryapi.dev/api/v2/entries/en/"


def fetch_examples(word):
    word_url = API_ADDRESS + word
    response = requests.get(word_url)
    if response.status_code == 200:
        data = response.json()
        return find_examples(data)
    else:
        return None


def find_examples(data):
    examples = []
    for m in data[0]["meanings"]:
        for d in m["definitions"]:
            if "example" in d:
                examples.append(d["example"])
    return examples


# =================================================================
# fetching word translations from yandex
# =================================================================

from os import getenv
import urllib.parse
from urllib.request import urlopen
import json


YANDEX_TOKEN = getenv("yandex_dict_token")
YANDEX_URL = f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={YANDEX_TOKEN}&lang=en-ru&text="


def translate(word, is_russian):
    url = YANDEX_URL + urllib.parse.quote(word)
    if is_russian:
        url = url.replace("lang=en-ru", "lang=ru-en")
    contents = urlopen(url).read()
    response = json.loads(contents.decode("utf8"))
    definitions = response["def"]
    if definitions:
        return definitions[0]["tr"][0]["text"]
    else:
        return None

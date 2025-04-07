# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import re
import string

from word2number import w2n


def _is_potential_number(word: str) -> bool:
    # NOTE: text_to_num.alpha2digit already support similar function, but it met some problem processing "one".
    number_parts = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty",
        "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion", "trillion",
    ]
    return word.lower() in number_parts


def _convert_textual_numbers_to_numeric(sentence: str) -> str:
    words = sentence.split() if len(sentence) > 1 else [sentence]
    converted_words = []
    current_number_phrase = []

    for word in words:
        if _is_potential_number(word):
            current_number_phrase.append(word)
        else:
            if current_number_phrase:
                number_string = " ".join(current_number_phrase)
                try:
                    numeric_value = w2n.word_to_num(number_string)
                    converted_words.append(str(numeric_value))
                except ValueError:
                    converted_words.extend(current_number_phrase)
                current_number_phrase = []

            converted_words.append(word)

    if current_number_phrase:
        try:
            number_string = " ".join(current_number_phrase)
            numeric_value = w2n.word_to_num(number_string)
            converted_words.append(str(numeric_value))
        except ValueError:
            converted_words.extend(current_number_phrase)

    return ' '.join(converted_words)


def normalize_answer(answer: str) -> str:
    answer = str(answer)

    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(_convert_textual_numbers_to_numeric(answer)))))


def normalize_mask(mask: str) -> str:
    return mask.strip().upper()

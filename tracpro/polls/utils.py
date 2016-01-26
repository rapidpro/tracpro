import math
import re

from decimal import InvalidOperation
import pycountry
import stop_words


def auto_range_categories(value_min, value_max):
    """
    Tries to pick sensible numerical range categories for the given range of
    values.
    """
    value_range = value_max - value_min
    if value_range > 1:
        # 10, 100, etc
        category_range = int(math.pow(10, math.ceil(math.log10(value_range))))

        if value_range < category_range / 2:
            category_range /= 2  # 5, 10, 50, 100 etc
    else:
        category_range = 5

    category_step = category_range / 5  # aim for 5 categories

    category_min = value_min - (value_min % category_step)

    category_max = category_min + category_step * 5

    # may need an extra category to hold max value
    while category_max <= value_max:
        category_max += category_step

    return category_min, category_max, category_step


def extract_words(text, language):
    """
    Extracts significant words from the given text (i.e. words we want to
    include in a word cloud)
    """
    ignore_words = []
    if language:
        code = pycountry.languages.get(bibliographic=language).alpha2
        try:
            ignore_words = stop_words.get_stop_words(code)
        except stop_words.StopWordError:
            pass

    words = re.split(r"[^\w'-]", text.lower(), flags=re.UNICODE)
    ignore_words = ignore_words
    return [w for w in words if w not in ignore_words and len(w) > 1]


def _convert(text):
    """If text is numeric, convert to an integer. Otherwise, force lowercase."""
    return int(text) if text.isdigit() else text.lower()


def natural_sort_key(text):
    """Key to sort text in a humanized way, e.g., 11 should come before 100."""
    text = text or ""  # can't split None
    alphanumeric_parts = re.split("([0-9]+)", text)  # ab12cd34 -> ["ab", "12", "cd", "34", ""]
    return [_convert(t) for t in alphanumeric_parts if t]


def get_numeric_values(values):
    """Return all values that can be parsed as a float."""
    numeric = []
    for val in values:
        try:
            numeric.append(float(val))
        except (TypeError, ValueError, InvalidOperation):
            pass
    return numeric

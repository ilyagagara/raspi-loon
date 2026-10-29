# =-=-=-=-=-=-=-=-=-=-=.
# CODE BY              |
# ILYA.GAGARA          |
# https://azzikx.com/  |
# =-=-=-=-=-=-=-=-=-=-=.

from datetime import datetime

DATES = {
    "1" : "Январь",
    "2" : "Февраль",
    "3" : "Март",
    "4" : "Апрель",
    "5" : "Май",
    "6" : "Июнь",
    "7" : "Июль",
    "8" : "Август",
    "9" : "Сентябрь",
    "10" : "Октябрь",
    "11" : "Ноябрь",
    "12" : "Декабрь",
}

def get_date(text:str = "1.1", short=False):
    """Returns month name by number and date (12.10 = 12 Октября)"""

    splited = text.split(".")
    day = splited[0]
    month = splited[1] if len(splited) > 1 else None

    month_name = DATES.get(month, "?????")
    if short:
        return f"{day} {month and month_name[0:3] or ''}"
    else:
        return f"{day} {month and month_name or ''}"

def get_cur_date():
    """Return current date in DD.MM format"""
    curdate = datetime.now()

    day = curdate.day
    if day < 10: day = "0" + str(day)

    month = curdate.month
    if month < 10: month = "0" + str(month)

    return f"{day}.{month}"
    #return "25.10"

def less_count(lessons):
    """Returns count of lessons with "Пара" (or "Нет занятий") text"""
    count = len(lessons)

    if count == 0:
        return "Нет занятий"

    return f"{count} {count == 1 and 'пара' or 'пары'}"

def short(text, limit=25):
    """Returns cutted text with dots at the end"""
    if len(text) <= limit:
        return text
    else:
        return text[0:limit] + "..."

def short_name(raw_name: str) -> str:
    """Makes full name shorter (ex: M. A. Ivan)"""
    if not raw_name or not raw_name.strip():
        return ""

    parts = raw_name.split()

    if len(parts) == 1:
        return parts[0].capitalize()

    last_name = parts[0].capitalize()

    initials = []
    for part in parts[1:]:
        subparts = part.split("-")
        sub_initials = [f"{sp[0].upper()}." for sp in subparts if sp]

        if sub_initials:
            initials.append("-".join(sub_initials))

    return f"{last_name} {' '.join(initials)}"

def safe_get(cur_list:list, index:int, default=None):
    """Returns default if index out of range"""

    if index >= len(cur_list) or index < 0:
        return default
    else:
        return cur_list[index]


ERRORS = {
    "connection" : "Ошибка подключения",
    "auth" : "Ошибка входа. Возможно неверные данные",
    "unknown" : "Неизвестная ошибка",
    "update" : "При обновлении расписания произошла ошибка."
}
def get_error_text(title:str):
    """Return error information"""

    if ERRORS.get(title):
        return ERRORS[title]
    else:
        return ERRORS['unknown']
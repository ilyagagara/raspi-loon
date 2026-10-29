import requests
import json
import re
from bs4 import BeautifulSoup
from pathlib import Path
from time import time

from threading import Lock

BASE_DIR = Path(__file__).resolve().parent
ENV_DIR = BASE_DIR / ".env"

LAST_RASP_PATH = BASE_DIR / "saves" / "last_rasp.json"
USER_DATA_PATH = BASE_DIR / "saves" / "userdata.json"


UPD_TIME_LIMIT = 300
USE_LAST_ONLY = False # Test Setting

file_lock = Lock()

def readJSON(path) -> dict | list:
    """Returns JSON file content"""
    try:
        with open(path, 'r', encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("read error", e)
        return False

def writeJSON(path, data):
    """Writes content to JSON file"""
    with file_lock:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                return True
        except Exception as e:
            print("write error", e)
            return False

def updateJSON(path, replace:dict):
    """Updates indexes in JSON file; replace = {"indextoupdate" : value}"""
    data = readJSON(path) or {}

    for index, value in replace.items():
        data[index] = value

    writeJSON(path, data)

def is_logged() -> bool:
    userdata = readJSON(USER_DATA_PATH) or {}
    return bool(userdata.get('login') and userdata.get('password'))

def set_login(login, password, log_res):
    res = doAuth(login, password)

    if res:
        updateJSON(
            USER_DATA_PATH,
            {'login' : login, 'password' : password}
        )

    log_res(res)

def can_update() -> bool:
    data = readJSON(USER_DATA_PATH) or {}
    
    lastupd = data.get("last_update") or 0
    curtime = int(time())

    return curtime - lastupd > UPD_TIME_LIMIT

def update_last():
    curtime = int(time())

    updateJSON(
        USER_DATA_PATH,
        {'last_update' : curtime}
    )

def parse_schedule(html_text: str) -> dict:
    """ Parsing Dashboard Lessons HTML to Dict """
    soup = BeautifulSoup(html_text, "html.parser")
    schedule = {}

    day_wraps = soup.select(".sch-mob .lessons_wrap")
    dayweek = 0

    for day in day_wraps:
        date_key = day.get("id")
        lessons_list = []

        dayweek += 1
        if dayweek > 7:
            continue

        blocks = day.select(".lesson_block")
        for block in blocks:
            title_elem = block.select_one(".lesson_title")

            # Если день пустой или нет заголовка
            if not title_elem or "Нет занятий" in title_elem.text:
                continue

            name_elem = block.select_one(".lesson_name")
            subject = name_elem.get_text(strip=True) if name_elem else ""

            start_time, end_time = "", ""
            for row in block.select("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and "время" in th.get_text(strip=True).lower() and td:
                    time_match = re.search(
                        r"(\d{1,2}:\d{2})\s*[-—]\s*(\d{1,2}:\d{2})", td.get_text()
                    )
                    if time_match:
                        start_time, end_time = time_match.groups()
                        break

            teacher_elem = block.select_one(".teacher")
            teacher = teacher_elem.get_text(strip=True) if teacher_elem else ""
            aud = title_elem.get_text(strip=True).replace("\n", "") if title_elem else ""
            aud = " ".join(aud.split())

            lessons_list.append([aud, subject, start_time, end_time, teacher])

        # 3. Запись расписания дня — СТРОГО ВНЕ цикла 'for block'
        schedule[date_key] = lessons_list

    return schedule

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://disto.mveu.ru/login"  # частая проверка на стороне сервера
})

def doAuth(login=None, password=None):
    """Authorization"""

    userdata = readJSON(USER_DATA_PATH) or {}
    if userdata and userdata.get("cookie"):
        print("Testing cookie")

        cookie = userdata.get("cookie");
        if cookie:
            session.cookies.set(
                "InStudy", 
                cookie, 
                domain="disto.mveu.ru"
            )

            data = getLessons(True)
            if data and not data.get("err"):
                print("Cookie is avalible!")
                return True
            else:
                print("Cookie is not avalible anymore!")

    print("Authorization process...")
    userdata = readJSON(USER_DATA_PATH) or {}
    payload = {
        "email" : login or userdata.get("login", "none"),
        "password" : password or userdata.get("password", "none")
    }

    try:
        resp = session.post("https://disto.mveu.ru/login/auth", data=payload)

        if "Расписание" in resp.text:
            newCookie = session.cookies.get_dict().get("InStudy")
            print("Newcookie!")

            if newCookie:
                userdata['cookie'] = newCookie
                writeJSON(USER_DATA_PATH, userdata)

            return True
        else:
            print("Authorization error")
            return False
        
    except Exception as e:
        print("Auth error:", e)
        return False
    

def getSchedule():
    return readJSON(LAST_RASP_PATH) or {}

def writeSchedule(page, data):
    page = str(page)

    curRasp = getSchedule()

    curRasp[page] = data
    writeJSON(LAST_RASP_PATH, curRasp)

def getLessons(test=False, page=0):
    if USE_LAST_ONLY:
        return {'list' : readJSON(LAST_RASP_PATH).get("0", {})}

    resp = session.get(f"https://disto.mveu.ru/schedule?skip={page}")
    output = {}

    if resp.status_code == 200 and "Расписание" in resp.text:
        parsed = parse_schedule(resp.text)

        if parsed:
            writeSchedule(page, parsed)
            update_last()

            output["list"] = parsed
        else:
            output["err"] = 'nolessons'
    elif resp.status_code == 200:
        print("Not authorized")

        if not test:
            res = doAuth()
            if res:
                return getLessons(page=page)
            else:
                output["err"] = 'auth'
    else:
        output['err'] = 'connection'

        last = readJSON(LAST_RASP_PATH)
        if last:
            output['list'] = last

    return output

def updateSchedule():
    for i in range(3):
        target_page = i-1
        try:
            res = getLessons(page = target_page)
            if res.get("err"):
                return False, res["err"]

            print(target_page, "page was updated")
            
        except Exception as e:
            cls = e.__class__
            error_title = f"{cls.__module__}.{cls.__name__}"
            
            return False, f"{error_title}: {e}"

    return True, "Success"
import requests
import json
import re
from bs4 import BeautifulSoup
from pathlib import Path
from time import time

from os import path, makedirs
from threading import Lock
from modules.texter import timestamp_date


BASE_DIR = Path(__file__).resolve().parent
if not path.exists(BASE_DIR / "saves"):
    makedirs(BASE_DIR / "saves")

LAST_RASP_PATH = BASE_DIR / "saves" / "last_rasp.json"
USER_DATA_PATH = BASE_DIR / "saves" / "userdata.json"

UPD_TIME_LIMIT = 1800
USE_LAST_ONLY = False # Test Setting

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://disto.mveu.ru/login"
}

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

MAIN_PAGE = ["Расписание"]
LOGIN_FORM = ["Логин", "Пароль", "Вход", "Забыли пароль?"]

def check_page(html_text:str, words:list):
    finds = 0
    for word in words:
        if word in html_text: finds += 1

    return finds >= len(words) / 2

class Student():
    """If login and password is None when using Saved Data from `saves/userdata.json`"""
    def __init__(self):
        self.login = None
        self.password = None

        self.last_upd = None
        session = requests.Session()
        
        session.headers.update(HEADERS)
        self.session = session

        data = readJSON(USER_DATA_PATH) or {}
        if data.get("login") and data.get("password"):
            self.login = data.get("login")
            self.password = data.get("password")

    def is_logged(self) -> bool:
        return bool(self.login and self.password)

    def set_login(self, login, password):
        res = self._do_auth(login, password)

        if res:
            updateJSON(
                USER_DATA_PATH,
                {'login' : login, 'password' : password}
            )

            self.login = login
            self.password = password

        return res

    def get_last_upd(self) -> int:
        """Return last update in unix time"""
        if not self.last_upd:
            data = readJSON(USER_DATA_PATH) or {}
            self.last_upd = data.get("last_update") or 0

        return self.last_upd

    def can_update(self) -> bool:
        last_upd = self.get_last_upd()
        curtime = int(time())

        return curtime - last_upd > UPD_TIME_LIMIT

    def _update_last(self):
        curtime = int(time())
        self.last_upd = curtime

        updateJSON(
            USER_DATA_PATH,
            {'last_update' : curtime}
        )

    def _parse_schedule(self, html_text: str) -> dict:
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

            schedule[date_key] = lessons_list

        return schedule

    def _do_auth(self, login=None, password=None):
        """Authorization"""

        userdata = readJSON(USER_DATA_PATH) or {}
        if userdata and userdata.get("cookie"):
            print("Testing cookie")

            cookie = userdata.get("cookie");
            if cookie:
                self.session.cookies.set(
                    "InStudy", 
                    cookie, 
                    domain="disto.mveu.ru"
                )

                data = self._get_lessons(True)
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
            resp = self.session.post("https://disto.mveu.ru/login/auth", data=payload, allow_redirects=True)

            if not check_page(resp.text, LOGIN_FORM):
                newCookie = self.session.cookies.get_dict().get("InStudy")
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
        

    def get_schedule(self):
        return readJSON(LAST_RASP_PATH) or {}

    def _write_schedule(self, page, data):
        page = str(page)

        curRasp = self.get_schedule()

        curRasp[page] = data
        writeJSON(LAST_RASP_PATH, curRasp)

    def _get_lessons(self, test=False, page=0, on_upd:function=None):
        if USE_LAST_ONLY:
            return {'list' : readJSON(LAST_RASP_PATH).get("0", {})}

        url = f"https://disto.mveu.ru/schedule?skip={page}"
        resp = self.session.get(url)
        output = {}

        if resp.status_code == 200 and check_page(resp.text, MAIN_PAGE):
            parsed = self._parse_schedule(resp.text)

            if parsed:
                self._write_schedule(page, parsed)
                self._update_last()

                output["list"] = parsed
            else:
                output["err"] = 'nolessons'
        elif resp.status_code == 200:
            print("Not authorized")

            if not test:
                on_upd("Вход в аккаунт...")
                res = self._do_auth()
                if res:
                    return self._get_lessons(page=page, on_upd=on_upd)
                else:
                    output["err"] = 'auth'
        else:
            output['err'] = 'connection'

            last = readJSON(LAST_RASP_PATH)
            if last:
                output['list'] = last

        return output

    def update_schedule(self, on_upd:function=None):
        if not self.is_logged():
            return False, "notauthed"

        cur_schedlue = self.get_schedule()
        today:dict = cur_schedlue.get("0", {})

        upd_date = timestamp_date(self.last_upd or 0)

        full_update = not (upd_date in today.keys())
        do_range = full_update and range(3) or range(1, 3)

        print("Doing", "full" if full_update else "part", "update")

        for i in do_range:
            target_page = i-1
            try:
                res = self._get_lessons(page = target_page, on_upd=on_upd)
                if res.get("err"):
                    return False, res["err"]
                else:
                    on_upd(f"{target_page + 2} / 3")

                print(target_page, "page was updated")
            except requests.exceptions.ConnectionError:
                return False, "connection"
            except Exception as e:
                cls = e.__class__
                error_title = f"{cls.__module__}.{cls.__name__}"
                
                return False, f"{error_title}: {e}"

        return True, "success"

    def reset_all(self):
        writeJSON(USER_DATA_PATH, {})
        writeJSON(LAST_RASP_PATH, {})
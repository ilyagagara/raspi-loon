# =-=-=-=-=-=-=-=-=-=-=.
# CODE BY              |
# ILYA.GAGARA          |
# https://azzikx.com/  |
# =-=-=-=-=-=-=-=-=-=-=.
# > Thanks for using RasPi-Loon!

# Main Code
import flet as ft

APP_VERSION = "1.0.0"
UPD_TEXT = "Идёт обновление расписания..."
LATEST_UPD_URL = "https://api.github.com/repos/ilyagagara/RasPi-Loon/releases/latest"
RELEASES_URL = "https://github.com/ilyagagara/raspi-loon/releases/"
MENU = [
    [ft.Icons.NEWSPAPER, "Расписание", "schedule"],
    [ft.Icons.BOOK, "Дневник", "wip"],
    [ft.Icons.SETTINGS, "Настройки", "wip"],
    [ft.Icons.LOGOUT, "Сменить Данные", "logout"]
]

from threading import Thread


import modules.classes as cs
import modules.texter as txt
import mveudisto

from requests import get
from time import time

def is_latest_version():
    try:
        response = get(LATEST_UPD_URL)
        data:dict = response.json()
        version = data.get("tag_name")

        if not version:
            return True, APP_VERSION

        print("latest version:", version, "current version:", APP_VERSION)
        return (version == APP_VERSION), version

    except Exception as e:
        print("error while getting version:", e)
        return True, APP_VERSION

class PageContent():
    def __init__(self, page:ft.Page, reset_call:function):
        self.page = page
        self.reset_call = reset_call

        # TOP-BAR
        func = lambda e: self._page_change(e.control.data)
        self.topbar = cs.TopBar(func)
        self.backtopbar = cs.TopBar(func, True)

        # BURGER-LIST
        self.burgermenu = cs.BurgerMenu(MENU, self._page_change)

        # STATUS WINDOW
        self.status = cs.StatusWindow()
        page.bottom_appbar = self.status

        # MVEU STUDENT
        student = mveudisto.Student()
        self.student = student

        # WIP WINDOW
        wip = cs.WorkInProgress()
        self.wip = wip

        # SCHEDULE
        self.schedule = cs.Schedule(self.student)

        # FLOATING ACTION BUTTON
        def _on_click(e:ft.Event):
            if student.can_update():
                self.update_schedule()
            else:
                self.status.show(
                f"Расписание можно обновлять **раз в 30 минут**",
                ft.Icons.ERROR, 4,
                priority=2)

        fbtn = ft.FloatingActionButton(
            ft.Icon(ft.Icons.AUTORENEW),
            on_click=_on_click
        )
        page.floating_action_button = fbtn
        self.fbtn = fbtn

        # LOGIN FORM
        self.last_try = 0
        self.trying = False
        def on_login(login, password):
            if self.trying: return

            if time() - self.last_try < 5:
                self.status.show("Нажимать можно раз в 5 секунд", ft.Icons.ERROR, 3, True)
                return

            self.last_try = time()
            self.trying = True

            self.status.show("Попытка входа...", ft.Icons.AUTORENEW)

            Thread(target=self._try_login, args=[login, password]).start()
    
        self.login = cs.LoginForm(on_login)

        # PAGES
        self.allelements = [
            self.topbar, self.backtopbar, self.schedule, self.login, self.wip, self.burgermenu, 
        ]
        self.pagesdata = {
            "login" : [self.login],
            "schedule" : [self.topbar, self.schedule],
            "wip" : [self.backtopbar, self.wip],
            "menu" : [self.burgermenu]
        }

        # BASE
        self.base = ft.Column(
            controls=self.allelements,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        # BASE CONTAINER
        self.base_container = ft.Container(
            self.base,
            width=600,
            expand=True,
            alignment=ft.Alignment.CENTER
        )

        page.add(self.base_container)

        Thread(target=self._check_version).start()
        self.updating = False
        self.is_logged = student.is_logged()
        self.lastpage = "schedule"
        self.curpage = "schedule" if self.is_logged else "login"

    def _check_version(self):
        is_latest, version = is_latest_version()
        cur_date = txt.get_cur_date()

        user_data = mveudisto.readJSON(mveudisto.USER_DATA_PATH) or {}
        last_notify = user_data.get("last_notify")

        if not is_latest and last_notify != cur_date:
            def _on_click(e):
                self.page.pop_dialog()
                if e.control.data == "cancel":
                    mveudisto.updateJSON(
                        mveudisto.USER_DATA_PATH,
                        {"last_notify" : cur_date}
                    )

            dialog = ft.AlertDialog(
                ft.Text(f"Доступна новая версия RasPi-Loon {version}!\n(текущая версия: {APP_VERSION})"),
                title="Обновление",
                actions=[
                    ft.Button("Напомнить Завтра", on_click=_on_click, data="cancel"),
                    ft.FilledButton("Скачать", on_click=_on_click, data="download", url=RELEASES_URL)
                ]
            )

            self.page.show_dialog(dialog)

    def _try_login(self, login, password):
        res = self.student.set_login(login, password)

        self.trying = False
        if not res:
            self.status.show("Не удалось войти! Точно верные данные?", ft.Icons.ERROR, 5, True)
            return

        self.curpage = "schedule"
        self.is_logged = True
        self.first_update()

        def close_d(e):
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            title="Привет!",
            content=ft.Text("Спасибо, что доверяешь RasPi-Loon! Надеюсь это упростит тебе учёбу! Пользуйся с удовольствием!"),
            actions=[
                ft.FilledButton("Спасибо", on_click=close_d),
            ]
        )

        self.page.show_dialog(dialog)
        return True
    
    def update_schedule(self, offline=False, manual:bool=False):
        self.fbtn.visible = False
        self.fbtn.update()

        self.updating = True

        if not offline:
            self.status.show(
                UPD_TEXT + " 0 / 3", ft.Icons.AUTORENEW,
                priority=2, easy_priority=True
            )

        curdate = txt.get_cur_date()
        def _upd_res(suc:bool, err:str=None, progress:bool=False):
            if self.curpage == "schedule" and not progress:
                self.fbtn.visible = True
                self.fbtn.update()
                self.updating = False

            if not suc:
                errinfo = txt.get_error_text(err)

                print("update error: ", err)
                if err == "found":
                    if offline:
                        errinfo = f"Расписание на {txt.get_date(curdate)} не найдено! Обновите расписание."
                    else:
                        return

                self.status.show(f"**{errinfo}**", ft.Icons.ERROR, 10, True, priority=3, easy_priority=True)
            else:
                if not progress:
                    if err == "declined":
                        self.status.show(
                            f"**Расписание недавно обновлено.** Авто-обновление не произошло",
                            ft.Icons.INFO, 10,
                            priority=2)
                    elif not offline:
                        self.status.show(f"**Расписание обновлено**", ft.Icons.CHECK_CIRCLE_OUTLINE, 10)
                else:
                    self.status.show(
                        UPD_TEXT + err, ft.Icons.AUTORENEW,
                        priority=2, easy_priority=True)

        self.schedule.update_schedule(offline, manual, _upd_res)

    def _reset_data(self):
        def _on_click(e:ft.Event):
            self.page.pop_dialog()

            data = e.control.data
            if data == "cancel": return

            self.student.reset_all()
            self.student = None

            self.page.remove(self.base_container)
            self.reset_call()

        dialog = ft.AlertDialog(
            ft.Markdown("Нажав **Изменить** данные от аккаунта и сохраненое расписание удалятся. Вам придеться вводить данные от аккаунт заново"),
            title="Уверены?",
            actions=[
                ft.Button("Отмена", data="cancel", on_click=_on_click),
                ft.FilledButton("Изменить", on_click=_on_click)
            ]
        )
        self.page.show_dialog(dialog)
    
    def _page_change(self, to:str):
        if to == "logout":
            self._reset_data()
            return

        if to:
            if to == "back":
                self.curpage = self.lastpage
            else:
                self.lastpage = self.curpage
                self.curpage = to
        else:
            self.curpage = "schedule"
        self.update_page()

    def update_page(self):
        curpage = self.curpage

        # Hiding elements
        for element in self.allelements:
            element.visible = False

        # Showing elements on cur page
        to_show = self.pagesdata.get(curpage, [])
        for element in to_show:
            element.visible = True

        # FButton
        self.fbtn.visible = curpage == "schedule" and not self.updating

        # Updating Page
        self.page.update()

    def first_update(self):
        if self.is_logged:
            self.update_schedule(True)
            self.update_schedule(False)

        self.update_page()

def main(page: ft.Page):
    print("> START -", page.session.id)

    page.fonts = {'GoogleSans' : "GoogleSans-Regular.ttf"}
    page.theme = ft.Theme(
        font_family="GoogleSans"
    )
    page.padding = ft.Padding.only(top=50)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.clean()

    pg = PageContent(page, lambda: main(page))
    pg.first_update()

ft.run(
    main,
    assets_dir="assets",
)
# =-=-=-=-=-=-=-=-=-=-=.
# CODE BY              |
# ILYA.GAGARA          |
# https://azzikx.com/  |
# =-=-=-=-=-=-=-=-=-=-=.
# > Thanks for using RasPi-Loon!

from threading import Thread

import flet as ft

import classes as cs
import mveudisto
import texter
from time import sleep

class PageContent():
    def __init__(self, page:ft.Page):
        self.page = page

        self.status = cs.StatusWindow()
        page.bottom_appbar = self.status
    
        self.schedule = cs.Schedule()
        page.floating_action_button = self.schedule.float_button
        page.add(self.schedule)

        def log_res(res):
            self.trying = False
            if not res:
                self.status.show("Не удалось войти! Точно верные данные?", ft.Icons.ERROR, 5, True)
                return

            self.update_page()

            def close_d(e):
                page.pop_dialog()

            dialog = ft.AlertDialog(
                title="Привет!",
                content=ft.Text("Спасибо, что доверяешь RasPi-Loon! Надеюсь это упростит тебе учёбу! Пользуйся с удовольствием!"),
                actions=[
                    ft.FilledButton("Спасибо", on_click=close_d),
                ]
            )

            page.show_dialog(dialog)
            return True

        self.trying = False
        def on_login(login, password):
            if self.trying: return
            self.trying = True

            self.status.show("Попытка входа...", ft.Icons.AUTORENEW)

            Thread(target=mveudisto.set_login, args=[login, password, log_res]).start()
    
        self.login = cs.LoginForm(on_login)
        page.add(self.login)

    def update(self, first_load=False, auto=False):
        if not first_load:
            self.status.show("Идёт обновление расписания...", ft.Icons.AUTORENEW)

        curdate = texter.get_cur_date()

        if auto:
            suc, err = self.schedule.update_attempt()
        else:
            suc, err = self.schedule.update_start(first_load)

        if not suc:
            errinfo = texter.get_error_text(err)

            print("update error: ", err)
            if err == "found":
                if first_load:
                    errinfo = f"Расписание на {texter.get_date(curdate)} не найдено! Обновите расписание."
                else:
                    return

            self.status.show(f"**{errinfo}**", ft.Icons.ERROR, 10, True)
        else:
            if err == "declined":
                self.status.show(f"**Расписание недавно обновлено.** Авто-обновление не произошло", ft.Icons.INFO, 10)
            else:
                self.status.show(f"**Расписание обновлено**", ft.Icons.CHECK_CIRCLE_OUTLINE, 10)
    
    def update_page(self):
        is_logged = mveudisto.is_logged()
        self.login.visible = not is_logged
        self.schedule.visible = is_logged
        self.page.floating_action_button.visible = is_logged

        if is_logged:
            self.update(first_load=True)
            Thread(target=self.update, args=[False, True]).start()

        self.page.update()


def main(page: ft.Page):
    page.fonts = {'GoogleSans' : "GoogleSans-Regular.ttf"}
    page.theme = ft.Theme(font_family="GoogleSans")
    page.padding = ft.Padding.only(top=50)

    page.clean()

    pg = PageContent(page)
    pg.update_page()

ft.run(
    main,
    assets_dir="assets",
    #host="0.0.0.0",
    #port=8550, 
    #view=ft.AppView.WEB_BROWSER,
)
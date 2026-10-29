# =-=-=-=-=-=-=-=-=-=-=.
# CODE BY              |
# ILYA.GAGARA          |
# https://azzikx.com/  |
# =-=-=-=-=-=-=-=-=-=-=.

import flet as ft
import texter as txt
from threading import Thread, Timer
import mveudisto

#region TopBar
class TopBar(ft.Container):
    def __init__(self, open_menu, **kwds):
        btn = ft.FilledButton(
            icon=ft.Icons.FORMAT_LIST_BULLETED_ROUNDED,
            on_click=open_menu
        )

        row = ft.Row(
            controls=[btn]
        )

        super().__init__(
            content=row,
            **kwds
        )

#region ArrowSelector
class ArrowSelector(ft.Row):
    def __init__(self, items: list[str] = [], on_change=None, **kwargs):
        self.items = items
        self.current_index = 0
        self.on_change_callback = on_change

        self.label = ft.Text(
            self.items[self.current_index] if self.items else "",
            size=18,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        self.btn_prev = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_size=28,
            on_click=self._prev_click,
        )

        self.btn_next = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_size=28,
            on_click=self._next_click,
        )

        super().__init__(
            controls=[
                self.btn_prev,
                ft.Container(
                    content=self.label,
                    alignment=ft.Alignment.CENTER,
                    width=170,
                ),
                self.btn_next,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            **kwargs,
        )
        self._update_buttons()
		
    def _prev_click(self, e):
        if self.current_index > 0:
            self.current_index -= 1
            self._apply_change()

    def _next_click(self, e):
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self._apply_change()

    def _apply_change(self):
        self.current_index = max(min(len(self.items) - 1, self.current_index), 0)

        if any(self.items):
            self.label.value = self.items[self.current_index]
        else:
            self.label.value = "None"
        
        self._update_buttons()
        self.update()
        if self.on_change_callback:
            self.on_change_callback(self.current_index, txt.safe_get(self.items, self.current_index, "None"))

    def _update_buttons(self):
        self.btn_prev.disabled = self.current_index == 0
        self.btn_next.disabled = self.current_index == len(self.items) - 1

    def update_items(self, new_items:list):
        self.items = new_items
        self._apply_change()

#region Lesson
class Lesson(ft.Container):
    def __init__(self, start_time = "??:??", end_time = "??:??", title = "???", aud = "???", teacher = "___", **kwargs):

        timeframe = ft.Column(
            controls=[
                ft.Text(start_time, size=28),
                ft.Divider(height=2,
                            thickness=1.5,
                            color=ft.Colors.WHITE,
                            opacity=0.5),
                ft.Text(end_time, size=28)
            ],
            width=80,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=3
        )

        infoframe = ft.Column(
            controls=[
                ft.Text(txt.short(title), size=20, weight=ft.FontWeight.BOLD),
                ft.Text(aud, size = 20),
                ft.Text(txt.short_name(teacher), size = 20, opacity=0.7)
            ],
            #horizontal_alignment=ft.CrossAxisAlignment.,
            spacing=2
        )

        frames = ft.Row(
            controls=[timeframe, infoframe],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        super().__init__(
            width=500,
            content=frames,
            padding=ft.Padding.only(left=30),
            **kwargs,
        )

#region LessonList
class LessonsList(ft.Container):
    def __init__(self, date: str, lessons: list = None, **kwargs):
        self.date = date
        self.lessons = lessons or []

        column_content = [
            ft.Text(f"{date}", size=23, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        ]

        size = len(self.lessons) - 1
        for i, item in enumerate(self.lessons):
            aud = txt.safe_get(item, 0)
            title = txt.safe_get(item, 1)
            start_time = txt.safe_get(item, 2)
            end_time = txt.safe_get(item, 3)
            teacher = txt.safe_get(item, 4)

            column_content.append(
                Lesson(start_time, end_time, title, aud, teacher)
            )
            if i < size:
                column_content.append(
                    ft.Container(ft.Divider(
                        ft.Colors.WHITE,
                        4,
                        thickness=2,
                        opacity=0.7
                    ),
                    width=500)
                )


        super().__init__(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                controls=column_content,
                spacing=5,
                expand=True
            ),
            expand=True,
            **kwargs,
        )

WEEK_NAMES = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
#region Schedule
class Schedule(ft.Container):
    # Updates Periods ("< 19 Oct - 25 Oct >" chooser)
    def update_periods(self, start_date = None, first_load=False):
        self.periods.clear()

        if not first_load:
            print("Updating")
            suc, err = mveudisto.updateSchedule()

            if not suc:
                print("error while updating:", err)
                return False, err

        schedule = mveudisto.getSchedule()

        start_index = None
        page_id = None
        sorted_keys = sorted(schedule.keys(), key=int)
        for key in sorted_keys:
            data:dict = schedule[key]

            keys = list(data.keys())
            first, last = keys[0], keys[-1]

            if start_date in keys:
                start_index = len(self.periods)
                page_id = key

            self.periods.append({
                'name' : f"{txt.get_date(first, True)} - {txt.get_date(last, True)}",
                'lessons' : data
                })

        if not page_id and any(sorted_keys):
            page_id = sorted_keys[0]

        self.arr_sel.update_items([p["name"] for p in self.periods])
        self.arr_sel.current_index = start_index or 0

        self.arr_sel._apply_change()

        is_found = self.update_tabs(schedule.get(str(page_id), {}), start_date)
        return is_found and start_index != None, "found"

    # Updates weeks schedlue
    def update_tabs(self, lessons, start_date = None):
        tab_headers = []
        tab_views = []

        start_index = None
        for i, (date, lessons_list) in enumerate(lessons.items()):
            if i >= 7:
                break

            if start_date == date:
                start_index = len(tab_headers)
            
            formdate = txt.get_date(date)
            lescount = txt.less_count(lessons_list)
            title = f"{formdate} - {lescount}"

            tab_label = WEEK_NAMES[i] if i < len(WEEK_NAMES) else f"Д{i+1}"
            tab_headers.append(ft.Tab(label=tab_label))

            tab_views.append(LessonsList(title, lessons_list))

        if not any(tab_headers):
            tab_headers.append(ft.Tab(label="Инфо"))
            tab_views.append(ft.Text("Расписание пустое"))

        self.tab_bar_view.controls = tab_views
        self.tab_bar.tabs = tab_headers

        self.tabs.length = len(tab_headers)
        self.tabs.selected_index = start_index or 0

        self.tabs.update()

        return start_index != None

    def update_start(self, first_load=False):
        curdate = txt.get_cur_date()

        return self.update_periods(curdate, first_load)
        

    def update(self, first_load=False):
        Thread(target=self.update_start, args=[first_load,]).start()

    def update_attempt(self):
        if mveudisto.can_update():
            return self.update_start()
        else:
            return True, "declined"
            print("Auto-update is declined")

    def on_lifecycle_change(self, e: ft.AppLifecycleStateChangeEvent):
        current_state = e.state

        if current_state == "resumed":
            self.update_attempt()

    def __init__(self, **kwargs):
        self.periods = []

        # Date Period Selector    
        def on_changed(index, _):
            if len(self.periods) > index:
                self.update_tabs(self.periods[index]['lessons'])

        self.arr_sel = ArrowSelector([], on_change=on_changed)

        # Floating Button
        def on_click_fbtn(e):
            self.update()

        self.float_button = ft.FloatingActionButton(
            ft.Icon(ft.Icons.AUTORENEW), on_click=on_click_fbtn
        )

        # Week Tabs
        self.tab_bar_view = ft.TabBarView(
            controls=[ft.Text("Идёт загрузка...")],
            expand=True,
        )
        self.tab_bar = ft.TabBar(
            tabs=[ft.Tab("Инфо")],
            scrollable=True,
            tab_alignment=ft.TabAlignment.CENTER,
        )

        self.tab_column = ft.Column(
            controls=[
                self.tab_bar,
                self.tab_bar_view
            ],
            expand=True)
        
        self.tabs = ft.Tabs(
            length=1,
            selected_index=0,
            content=self.tab_column,
            expand=True
            )

        super().__init__(
            content=ft.Column(
                controls=[
                    self.arr_sel,
                    ft.Container(
                        content=self.tabs,
                        expand=True,
                    )
                ],
                expand=True
            ),
            expand=True,
            **kwargs
        )

#region StatusWindow
class StatusWindow(ft.BottomAppBar):
    def __init__(self):
        self.statusid = 0
        self._timer = None

        self.icon = ft.Icon(ft.Icons.AUTORENEW)
        self.info = ft.Markdown("...", width=350)

        self.content_row = ft.Row(
            [self.icon, self.info],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )

        super().__init__(
            height=45,
            padding=ft.Padding(3),
            margin=ft.Margin.only(bottom=40),
            content=self.content_row,
            visible=True,
            bgcolor=ft.Colors.TRANSPARENT,
        )

    def hide_timeout(self, id):
        if self.statusid == id:
            self.content_row.visible = False
            self.bgcolor = ft.Colors.TRANSPARENT
            if self.page:
                self.update()

    def show(
        self,
        text: str = None,
        icon: ft.Icons = ft.Icons.INFO_OUTLINE,
        duration: float = None,
        is_error=False,
    ):
        if self._timer:
            self._timer.cancel()

        self.statusid += 1

        if text is None:
            self.content_row.visible = False
            self.bgcolor = ft.Colors.TRANSPARENT
        else:
            self.content_row.visible = True
            self.bgcolor = ft.Colors.RED_600 if is_error else ft.Colors.BLACK_54
            self.info.value = text
            self.icon.icon = icon

        print("new status", text)

        # Если страница доступна, обновляем контрол
        if self.page:
            self.update()

        if duration and text is not None:
            self._timer = Timer(duration, self.hide_timeout, [self.statusid])
            self._timer.start()

#region LoginForm
class LoginForm(ft.Container):
    def __init__(self, on_auth = None):
        self.on_auth = on_auth

        login_input = ft.TextField(hint_text="Обычно это Почта", label="Логин")
        password_input = ft.TextField(hint_text="Пароль", label="Пароль", password=True)
        save_btn = ft.Button(
            ft.Text("Сохранить", size=20),
            height=40
            )

        self.login = login_input
        self.password = password_input

        save_btn.on_click = self._on_click
        
        form = ft.Column(
            controls=[
                ft.Text("RasPi-Loon", size=40),
                ft.Text("Введите Данные от аккаунта InStudy"),
                login_input,
                password_input,
                save_btn
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        super().__init__(
            content=form,
            padding=3,
            visible=True,
            alignment=ft.Alignment.CENTER
        )

    def _on_click(self):
        login = self.login.value
        password = self.password.value

        if self.on_auth:
            self.on_auth(login, password)
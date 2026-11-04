# =-=-=-=-=-=-=-=-=-=-=.
# CODE BY              |
# ILYA.GAGARA          |
# https://azzikx.com/  |
# =-=-=-=-=-=-=-=-=-=-=.

# All screen elements stores here

import flet as ft
from threading import Thread, Timer

import modules.texter as txt
import mveudisto

#region LinkText
class LinkText(ft.Text):
    def __init__(self, text:str, url:str, **kwargs):
        super().__init__(
            spans=[
                ft.TextSpan(
                    text,
                    url=url,
                    style=ft.TextStyle(color=ft.Colors.BLUE, decoration=ft.TextDecoration.UNDERLINE, decoration_color=ft.Colors.BLUE),
                ),
            ],
            **kwargs
        )

#region TopBar
class TopBar(ft.Container):
    def __init__(self, call_back:function = None, back:bool=False, **kwds):
        if back:
            arrow = ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                data="back",
                on_click=call_back,
            )
            controls=[arrow]
        else:
            btn = ft.IconButton(
                icon=ft.Icons.FORMAT_LIST_BULLETED_ROUNDED,
                data="menu",
                on_click=call_back,
            )
            title = ft.Row(
                controls=[
                    ft.Text("RasPi-Loon"),
                    ft.Image(
                        "icon.svg",
                        height=40
                    )
                ]
            )
            notification = ft.IconButton(
                ft.Icons.NOTIFICATIONS,
                data="wip",
                on_click=call_back
            )
            controls=[btn, title, notification]

        row = ft.Row(
            controls=controls,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=True
        )

        super().__init__(
            content=row,
            padding=ft.Padding(left=15),
            **kwds
        )

#region BurgerMenu
RED_TEXT = ["logout"]
class BurgerMenu(ft.Container):
    def __init__(self, elements:list[list[ft.Icon, str]], callback:function, **kwds):
        controls = [ft.Text("RasPi-Loon", size=40)]

        def _on_click(e):
            d = e.control.data
            callback(d)

        for data in elements:
            icon, title = data[0], data[1]
            call_data = data[2] if len(data) >= 3 else None

            color = ft.Colors.RED if call_data in RED_TEXT else ft.Colors.ON_SURFACE
            row = ft.Button(
                ft.Row(
                    controls=[
                        ft.Icon(icon, scale=1.5, color=color),
                        ft.Text(title, size=20, color=color)
                    ],
                ),
                data=call_data,
                on_click=_on_click,
                height=50
            )

            controls.append(row)

        column = ft.Column(
            controls=controls,
            horizontal_alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
        
        super().__init__(
            content=column,
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=ft.Padding(left=20, right=20),
            **kwds
        )

#region WorkInProgress
class WorkInProgress(ft.Container):
    def __init__(self, **kwds):
        info = ft.Text("Страница в Разработке!", size=20)

        super().__init__(
            content=info,
            alignment=ft.Alignment.CENTER,
            expand=True,
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
            self._apply_change(True)

    def _next_click(self, e):
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self._apply_change(True)

    def _apply_change(self, clicked:bool=None):
        self.current_index = max(min(len(self.items) - 1, self.current_index), 0)

        if any(self.items):
            self.label.value = self.items[self.current_index]
        else:
            self.label.value = "None"
        
        self._update_buttons()
        self.update()
        if self.on_change_callback and clicked:
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
                            color=ft.Colors.ON_SURFACE,
                            opacity=0.5),
                ft.Text(end_time, size=28)
            ],
            width=80,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=3
        )

        infoframe = ft.Column(
            controls=[
                ft.Text(title, size=20, width=300, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
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
                    ft.Container(
                        ft.Divider(
                        ft.Colors.ON_SURFACE,
                        4,
                        thickness=2,
                        opacity=0.7
                    ),
                    width=380)
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
    def _update_tabs(self, offline:bool=None, start_date=None, lessons:list=None, on_upd:function=None):
        # > Updates periods
        start_index = None
        if not lessons:
            self.periods.clear()
            
            if not offline:
                print("Updating")
                suc, err = self.student.update_schedule(lambda mssg: on_upd(True, f" {mssg}", True))

                if not suc:
                    print("error while updating:", err)
                    return False, err

            schedule = self.student.get_schedule()

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

            lessons = schedule.get(str(page_id), {})
        found_period = bool(start_index)

        # > Updating Tabs
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

        found_date = bool(start_index)

        if not any(tab_headers):
            tab_headers.append(ft.Tab(label="Инфо"))
            tab_views.append(ft.Text("Расписание пустое"))

        self.tab_bar_view.controls = tab_views
        self.tab_bar.tabs = tab_headers

        self.tabs.length = len(tab_headers)
        self.tabs.selected_index = start_index or 0

        date = txt.timestamp_date(self.student.get_last_upd(), True)
        self.upddate.value = f"Последнее обновление: {date}"

        self.update()
        
        return (found_period and found_date), "found"
        
    def update_schedule(self, offline:bool=False, manual:bool=False, on_res:function = None):
        if not offline and not manual:
            if not self.student.can_update():
                on_res(True, "declined")
                print("Auto-update is declined")
                return

        curdate = txt.get_cur_date()

        def _start():
            data = self._update_tabs(offline, curdate, on_upd=on_res)

            if on_res:
                on_res(*data)

        if offline:
            _start()
        else:
            Thread(target=_start).start()

    def __init__(self, student:mveudisto.Student, **kwargs):
        self.student = student
        self.periods = []

        # Date Period Selector    
        def on_changed(index, _):
            if len(self.periods) > index:
                self._update_tabs(lessons=self.periods[index]['lessons'])

        self.arr_sel = ArrowSelector([], on_change=on_changed)

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

        self.upddate = ft.Text("", opacity=0.7)

        super().__init__(
            content=ft.Column(
                controls=[
                    self.arr_sel,
                    ft.Container(
                        content=self.tabs,
                        expand=True,
                    ),
                    self.upddate
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            ),
            expand=True,
            **kwargs
        )

#region StatusWindow
class StatusWindow(ft.BottomAppBar):
    def __init__(self):
        self.statusid = 0
        self._maxpriority = 0
        self._timer = None

        self.icon = ft.Icon(ft.Icons.AUTORENEW)
        self.info = ft.Markdown("...", width=350)

        self.content_row = ft.Row(
            [self.icon, self.info],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        super().__init__(
            height=45,
            opacity=0,
            animate_opacity=100,
            content=self.content_row,
            margin=ft.Margin.only(bottom=30),
            padding=ft.Padding(3),
        )

    def hide_timeout(self, id):
        if self.statusid == id:
            self._easyprority = False
            self._maxpriority = 0

            self.opacity = 0
            if self.page:
                self.update()

    def show(
        self,
        text: str = None,
        icon: ft.Icons = ft.Icons.INFO_OUTLINE,
        duration: float = None,
        is_error=False,
        priority:int=1,
        easy_priority:bool=False
    ):
        if self._maxpriority > priority and not self._easyprority:
            return

        self._easyprority = easy_priority
        self._maxpriority = priority
        
        if self._timer:
            self._timer.cancel()

        self.statusid += 1

        if text is None:
            self.opacity = 0
        else:
            self.opacity = 1
            self.bgcolor = ft.Colors.RED_600 if is_error else ft.Colors.BLACK_54
            self.info.value = text
            self.icon.icon = icon

        print("new status", text)

        if self.page:
            self.update()

        if duration and text is not None:
            self._timer = Timer(duration, self.hide_timeout, [self.statusid])
            self._timer.start()

#region LoginForm
class LoginForm(ft.SafeArea):
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
                save_btn,
                ft.Divider(
                    height=2,
                    opacity=0.5
                ),
                LinkText("Зачем нужны данные и Хранение данных", "https://github.com/ilyagagara/raspi-loon/blob/main/WHYDATA.md", size=13),
                ft.Text(
                    "Сделал Ilya Gagara\nв 2026",
                    opacity=0.5,
                    text_align=ft.TextAlign.CENTER,
                    size=10
                )
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )

        base = ft.Container(
            content=form,
            visible=True,
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
        
        super().__init__(
            content=base,
            expand=True
        )

    def _on_click(self):
        login = self.login.value
        password = self.password.value

        if self.on_auth:
            self.on_auth(login, password)
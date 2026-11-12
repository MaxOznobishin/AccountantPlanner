
import sqlite3
from resources import resource_path
from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, QDate, QTimer, QLocale, QSize
from PySide6.QtGui import QAction, QColor, QTextCharFormat, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QMainWindow,
    QLineEdit,
    QSizeGrip,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from database.db import (
    RECURRENCE_NAMES,
    delete_task,
    get_dashboard_stats,
    get_organizations,
    get_period_bounds,
    get_task,
    get_tasks,
    set_task_completed,
)

from services.notifications import NotificationService
from ui.settings import SettingsDialog
from ui.organizations import OrganizationsDialog
from ui.tasks import TaskForm
from ui.light_theme import STYLESHEET
from ui.calendar_v2 import PlannerCalendar
from ui.dropdown import ComboBox as QComboBox


class TitleBar(QFrame):
    """Панель для перемещения виджета."""

    def __init__(self, window):
        super().__init__(window)

        self.window_ref = window
        self.drag_offset = None

        self.setObjectName("titleBar")
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)

        title = QLabel("●  МОЙ ПЛАН")
        title.setObjectName("windowTitle")
        title.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.toggle_button = QPushButton("Планировщик")
        self.toggle_button.setObjectName("modeButton")
        self.toggle_button.clicked.connect(
            window.toggle_expanded
        )

        hide_button = QPushButton("–")
        hide_button.setObjectName("windowButton")
        hide_button.setFixedSize(34, 34)
        hide_button.setToolTip("Скрыть в трей")
        hide_button.clicked.connect(window.hide_to_tray)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeAppButton")
        self.close_button.setFixedSize(34, 34)
        self.close_button.setToolTip("Полностью закрыть приложение")
        self.close_button.clicked.connect(window.quit_application)

        layout.addWidget(title)
        layout.addStretch()
        settings_button = QPushButton()
        settings_button.setObjectName("settingsButton")
        settings_button.setIcon(QIcon(str(resource_path("ui/assets/settings.svg"))))
        settings_button.setIconSize(QSize(20, 20))
        settings_button.setFixedSize(34, 34)
        settings_button.setToolTip("Настройки приложения")
        settings_button.setAccessibleName("Настройки приложения")
        settings_button.clicked.connect(window.open_settings)
        layout.addWidget(settings_button)
        layout.addWidget(self.toggle_button)
        layout.addWidget(hide_button)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = (
                event.globalPosition().toPoint()
                - self.window_ref.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            self.drag_offset is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.window_ref.move(
                event.globalPosition().toPoint()
                - self.drag_offset
            )
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        event.accept()


class AccountantWidget(QMainWindow):
    """Планировщик задач с календарём и уведомлениями."""

    def __init__(self):
        super().__init__()

        self.expanded = False
        self.quitting = False
        self.tray = None
        self.current_period = "Сегодня"
        self.marked_dates = []
        self.compact_size = QSize(430, 470)
        self.expanded_size = QSize(620, 820)

        self.setWindowTitle("Бухгалтер — планировщик")

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(400)

        self.build_interface()
        self.apply_styles()
        self.create_tray()

        self.notification_service = NotificationService(
            self.tray
        )

        self.refresh_organizations()
        self.set_compact_mode()

        # Автоматическое обновление каждую минуту.
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(60_000)
        self.refresh_timer.timeout.connect(
            self.periodic_update
        )
        self.refresh_timer.start()

        # Первая проверка сразу после запуска.
        QTimer.singleShot(
            1000,
            self.periodic_update
        )

    # =====================================
    # ИНТЕРФЕЙС
    # =====================================

    def build_interface(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Компактный вид
        self.compact_panel = QWidget()
        self.compact_panel.setObjectName("compactPanel")
        compact_layout = QVBoxLayout(self.compact_panel)
        compact_layout.setContentsMargins(18, 16, 18, 16)
        compact_layout.setSpacing(12)

        compact_head = QHBoxLayout()
        compact_titles = QVBoxLayout()
        compact_titles.setSpacing(2)
        compact_title = QLabel("Сегодня")
        compact_title.setObjectName("compactTitle")
        self.date_label = QLabel()
        self.date_label.setObjectName("dateLabel")
        compact_titles.addWidget(compact_title)
        compact_titles.addWidget(self.date_label)
        quick_add = QPushButton()
        quick_add.setIcon(QIcon(str(resource_path("ui/assets/plus.svg"))))
        quick_add.setIconSize(QSize(24, 24))
        quick_add.setObjectName("quickAddButton")
        quick_add.setFixedSize(42, 42)
        quick_add.setToolTip("Новая задача")
        quick_add.clicked.connect(self.add_new_task)
        compact_head.addLayout(compact_titles)
        compact_head.addStretch()
        compact_head.addWidget(quick_add)
        compact_layout.addLayout(compact_head)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        today_card = QFrame()
        today_card.setObjectName("statCard")
        today_box = QVBoxLayout(today_card)
        today_box.setContentsMargins(12, 9, 12, 9)
        today_box.setSpacing(1)
        self.summary_label = QLabel()
        self.summary_label.setObjectName("statNumber")
        today_box.addWidget(self.summary_label)
        today_box.addWidget(QLabel("осталось сегодня"))

        overdue_card = QFrame()
        overdue_card.setObjectName("overdueCard")
        overdue_box = QVBoxLayout(overdue_card)
        overdue_box.setContentsMargins(12, 9, 12, 9)
        overdue_box.setSpacing(1)
        self.overdue_label = QLabel()
        self.overdue_label.setObjectName("statNumber")
        overdue_box.addWidget(self.overdue_label)
        overdue_box.addWidget(QLabel("просрочено"))
        stats_row.addWidget(today_card, 1)
        stats_row.addWidget(overdue_card, 1)
        compact_layout.addLayout(stats_row)

        compact_section = QHBoxLayout()
        compact_section.addWidget(QLabel("ЗАДАЧИ НА СЕГОДНЯ"))
        compact_section.addStretch()
        self.compact_count_label = QLabel()
        self.compact_count_label.setObjectName("mutedLabel")
        compact_section.addWidget(self.compact_count_label)
        compact_layout.addLayout(compact_section)

        compact_scroll = QScrollArea()
        compact_scroll.setWidgetResizable(True)
        compact_scroll.setFrameShape(QFrame.Shape.NoFrame)
        compact_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.compact_task_content = QWidget()
        self.compact_task_content.setObjectName("compactTaskContent")
        self.compact_task_layout = QGridLayout(self.compact_task_content)
        self.compact_task_layout.setColumnStretch(0, 1)
        self.compact_task_layout.setColumnStretch(1, 1)
        self.compact_task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.compact_task_layout.setContentsMargins(0, 0, 0, 0)
        self.compact_task_layout.setSpacing(6)
        compact_scroll.setWidget(self.compact_task_content)
        compact_layout.addWidget(compact_scroll, 1)

        self.next_task_label = QLabel()
        self.next_task_label.setObjectName("nextTaskLabel")
        self.next_task_label.setWordWrap(True)
        compact_layout.addWidget(self.next_task_label)

        main_layout.addWidget(self.compact_panel)

        # Расширенный вид
        self.expanded_panel = QWidget()
        expanded_layout = QVBoxLayout(
            self.expanded_panel
        )
        expanded_layout.setContentsMargins(
            18, 16, 18, 20
        )
        expanded_layout.setSpacing(10)

        header = QLabel("Планировщик")
        header.setObjectName("sectionTitle")
        expanded_layout.addWidget(header)
        subtitle = QLabel("Все задачи и сроки")
        subtitle.setObjectName("hintLabel")
        expanded_layout.addWidget(subtitle)

        # Переключатели периодов
        periods_layout = QHBoxLayout()
        periods_layout.setSpacing(5)

        self.period_buttons = {}

        for period in (
            "Сегодня",
            "Неделя",
            "Месяц",
            "Год",
            "Календарь"
        ):
            button = QPushButton(period)
            button.setCheckable(True)

            button.clicked.connect(
                lambda _checked=False, p=period:
                self.select_period(p)
            )

            self.period_buttons[period] = button
            periods_layout.addWidget(button)

        expanded_layout.addLayout(periods_layout)

        # Выбор организации
        org_layout = QHBoxLayout()

        self.org_combo = QComboBox()
        self.org_combo.currentIndexChanged.connect(
            self.refresh_task_area
        )

        manage_button = QPushButton("Организации")
        manage_button.clicked.connect(
            self.open_organizations
        )

        org_layout.addWidget(self.org_combo, 1)
        org_layout.addWidget(manage_button)

        expanded_layout.addLayout(org_layout)

        filters = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск задач и организаций")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.refresh_task_area)
        self.state_combo = QComboBox()
        self.state_combo.addItems(["Все задачи", "В работе", "Просроченные", "Выполненные"])
        self.state_combo.currentIndexChanged.connect(self.refresh_task_area)
        filters.addWidget(self.search_input, 1)
        filters.addWidget(self.state_combo)
        expanded_layout.addLayout(filters)

        # Календарь
        self.calendar = PlannerCalendar()
        self.calendar.setGridVisible(False)
        self.calendar.setLocale(QLocale("ru_RU"))
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setSelectedDate(
            QDate.currentDate()
        )
        self.calendar.setFixedHeight(355)

        self.calendar.selectionChanged.connect(
            self.on_calendar_selected
        )

        self.calendar.currentPageChanged.connect(
            self.on_calendar_page_changed
        )

        expanded_layout.addWidget(self.calendar)

        # Кнопка создания задачи
        new_task_button = QPushButton("+ Новая задача")
        new_task_button.setObjectName("newTaskButton")
        new_task_button.clicked.connect(
            self.add_new_task
        )
        expanded_layout.addWidget(new_task_button)

        # Список задач
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.task_content = QWidget()
        self.task_content.setObjectName("taskContent")

        self.task_layout = QGridLayout(
            self.task_content
        )
        self.task_layout.setColumnStretch(0, 1)
        self.task_layout.setColumnStretch(1, 1)
        self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_layout.setContentsMargins(
            2, 2, 2, 2
        )
        self.task_layout.setSpacing(8)

        scroll.setWidget(self.task_content)
        expanded_layout.addWidget(scroll, 1)

        self.status_label = QLabel()
        self.status_label.setObjectName("hintLabel")
        expanded_layout.addWidget(self.status_label)

        main_layout.addWidget(self.expanded_panel)
        grip_row = QHBoxLayout()
        grip_row.addStretch()
        grip_row.addWidget(QSizeGrip(self))
        main_layout.addLayout(grip_row)

        self.select_period("Сегодня")

    # =====================================
    # ОРГАНИЗАЦИИ
    # =====================================

    def refresh_organizations(self):
        selected_id = self.org_combo.currentData()

        self.org_combo.blockSignals(True)
        self.org_combo.clear()

        self.org_combo.addItem(
            "Все организации", None
        )

        for org in get_organizations():
            self.org_combo.addItem(
                org["name"], org["id"]
            )

        index = self.org_combo.findData(selected_id)

        self.org_combo.setCurrentIndex(
            index if index >= 0 else 0
        )
        self.org_combo.blockSignals(False)

        self.refresh_task_area()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def open_organizations(self):
        dialog = OrganizationsDialog(self)
        dialog.exec()
        self.refresh_organizations()

    # =====================================
    # ПЕРИОДЫ И КАЛЕНДАРЬ
    # =====================================

    def select_period(self, period):
        self.current_period = period

        for name, button in self.period_buttons.items():
            button.setChecked(name == period)

        self.calendar.setVisible(
            period == "Календарь"
        )

        if self.expanded:
            self.setMinimumHeight(800 if period == "Календарь" else 600)

        self.refresh_task_area()

    def on_calendar_selected(self):
        if self.current_period != "Календарь":
            self.select_period("Календарь")
        else:
            self.refresh_task_area()

    def on_calendar_page_changed(self, year, month):
        self.refresh_calendar_marks()

    def get_selected_bounds(self):
        if self.current_period != "Календарь":
            return get_period_bounds(
                self.current_period
            )

        qdate = self.calendar.selectedDate()

        selected = date(
            qdate.year(),
            qdate.month(),
            qdate.day()
        )

        next_day = selected + timedelta(days=1)

        return (
            f"{selected:%Y-%m-%d} 00:00:00",
            f"{next_day:%Y-%m-%d} 00:00:00"
        )

    def refresh_calendar_marks(self):
        """Выделяет даты с задачами в календаре."""

        if not hasattr(self, "calendar"):
            return

        # Убираем выделение предыдущего месяца.
        default_format = QTextCharFormat()

        for qdate in self.marked_dates:
            self.calendar.setDateTextFormat(
                qdate, default_format
            )

        self.marked_dates = []

        year = self.calendar.yearShown()
        month = self.calendar.monthShown()

        first_day = date(year, month, 1)

        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        start_at = (
            f"{first_day:%Y-%m-%d} 00:00:00"
        )
        end_at = (
            f"{next_month:%Y-%m-%d} 00:00:00"
        )

        tasks = get_tasks(
            start_at,
            end_at,
            self.org_combo.currentData()
        )

        # Сколько задач на каждой дате и есть ли
        # хотя бы одна невыполненная.
        day_status = {}

        for task in tasks:
            day = datetime.strptime(
                task["due_at"],
                "%Y-%m-%d %H:%M:%S"
            ).date()

            if day not in day_status:
                day_status[day] = False

            if task["completed_at"] is None:
                day_status[day] = True

        for day, has_pending in day_status.items():
            qdate = QDate(
                day.year, day.month, day.day
            )

            fmt = QTextCharFormat()

            if has_pending:
                fmt.setBackground(
                    QColor("#285a87")
                )
            else:
                fmt.setBackground(
                    QColor("#235947")
                )

            fmt.setForeground(
                QColor("#ffffff")
            )

            self.calendar.setDateTextFormat(
                qdate, fmt
            )
            self.marked_dates.append(qdate)

    # =====================================
    # СОЗДАНИЕ И РЕДАКТИРОВАНИЕ ЗАДАЧ
    # =====================================

    def add_new_task(self):
        if not get_organizations():
            QMessageBox.information(
                self,
                "Нет организаций",
                "Сначала добавьте организацию."
            )
            return

        dialog = TaskForm(
            self,
            initial_organization_id=(
                self.org_combo.currentData()
            )
        )

        if dialog.exec() == TaskForm.DialogCode.Accepted:
            self.refresh_task_area()

    def edit_task(self, task_id):
        task = get_task(task_id)

        if task is None:
            self.refresh_task_area()
            return

        dialog = TaskForm(self, task=task)

        if dialog.exec() == TaskForm.DialogCode.Accepted:
            self.refresh_task_area()

    def remove_task(self, task_id):
        task = get_task(task_id)

        if task is None:
            return

        if task["recurrence"] != "none":
            message = (
                f"Удалить всю регулярную задачу "
                f"«{task['title']}»?\n\n"
                "История выполнений также "
                "будет удалена."
            )
        else:
            message = (
                f"Удалить задачу «{task['title']}»?"
            )

        reply = QMessageBox.question(
            self,
            "Удаление задачи",
            message,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_task(task_id)

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.warning(
                self,
                "Ошибка удаления",
                str(error)
            )
            return

        self.refresh_task_area()

    def toggle_completion(
        self,
        task_id,
        occurrence_due_at,
        checked
    ):
        try:
            set_task_completed(
                task_id,
                checked,
                occurrence_due_at
            )

        except (sqlite3.Error, ValueError) as error:
            QMessageBox.warning(
                self,
                "Ошибка сохранения",
                str(error)
            )

        self.refresh_task_area()

    # =====================================
    # СПИСОК ЗАДАЧ
    # =====================================

    def clear_task_list(self):
        while self.task_layout.count():
            item = self.task_layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.hide()
                widget.deleteLater()

    def refresh_task_area(self, *_):
        if not hasattr(self, "task_layout"):
            return

        self.clear_task_list()

        start_at, end_at = self.get_selected_bounds()

        tasks = get_tasks(
            start_at,
            end_at,
            self.org_combo.currentData()
        )

        now_str = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        total_tasks = len(tasks)
        query = self.search_input.text().strip().casefold()
        state = self.state_combo.currentIndex()
        tasks = [task for task in tasks if (
            (not query or query in " ".join(str(task.get(key) or "") for key in
             ("title", "organization_name", "description")).casefold())
            and (state == 0
                 or state == 1 and task["completed_at"] is None
                 or state == 2 and task["completed_at"] is None and task["due_at"] < now_str
                 or state == 3 and task["completed_at"] is not None)
        )]

        if not tasks:
            empty = QLabel(
                "Ничего не найдено. Измените фильтры."
                if total_tasks else "На этот период задач нет. Добавьте первую задачу."
            )
            empty.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            empty.setObjectName("emptyState")
            empty.setMinimumHeight(130)
            empty.setWordWrap(True)
            self.task_layout.addWidget(empty, 0, 0, 1, 2)

        for task_index, task in enumerate(tasks):
            frame = QFrame()
            frame.setObjectName("taskFrame")

            task_box = QVBoxLayout(frame)
            task_box.setContentsMargins(
                12, 12, 12, 12
            )
            task_box.setSpacing(5)

            checkbox = QCheckBox(task["title"])
            checkbox.setToolTip(task["title"])
            checkbox.setChecked(
                task["completed_at"] is not None
            )

            checkbox.toggled.connect(
                lambda checked,
                task_id=task["id"],
                due_at=task["instance_due_at"]:
                self.toggle_completion(
                    task_id, due_at, checked
                )
            )

            task_box.addWidget(checkbox)

            priority_text = {
                1: "Низкий",
                2: "Обычный",
                3: "Высокий"
            }[task["priority"]]

            recurrence_text = RECURRENCE_NAMES[
                task["recurrence"]
            ]

            due_text = datetime.strptime(
                task["due_at"],
                "%Y-%m-%d %H:%M:%S"
            ).strftime("%d.%m.%Y %H:%M")

            if task["completed_at"]:
                status = "Выполнена"
            elif task["due_at"] < now_str:
                status = "Просрочена"
            else:
                status = "В работе"

            frame.setProperty("state", "done" if task["completed_at"] else
                              "overdue" if task["due_at"] < now_str else "pending")
            badge = QLabel(status + "  ·  " + priority_text + " приоритет")
            badge.setObjectName("statusBadge")
            badge.setWordWrap(True)
            badge.setProperty("state", frame.property("state"))
            task_box.addWidget(badge)
            details = QLabel(
                f"{task['organization_name']}  ·  {due_text}\n"
                f"{recurrence_text}"
            )
            details.setTextFormat(Qt.TextFormat.PlainText)
            details.setObjectName("taskDetails")
            details.setWordWrap(True)

            task_box.addWidget(details)

            if task["description"]:
                description = QLabel(
                    task["description"]
                )
                description.setTextFormat(Qt.TextFormat.PlainText)
                description.setWordWrap(True)
                task_box.addWidget(description)

            actions = QHBoxLayout()

            edit_button = QPushButton("Изменить")
            edit_button.clicked.connect(
                lambda _=False, task_id=task["id"]:
                self.edit_task(task_id)
            )

            remove_button = QPushButton("Удалить")
            remove_button.setObjectName("dangerButton")
            remove_button.clicked.connect(
                lambda _=False, task_id=task["id"]:
                self.remove_task(task_id)
            )

            actions.addStretch()
            actions.addWidget(edit_button)
            actions.addWidget(remove_button)

            task_box.addLayout(actions)
            self.task_layout.addWidget(frame, task_index // 2, task_index % 2)

        completed = sum(
            task["completed_at"] is not None
            for task in tasks
        )

        self.status_label.setText(
            f"Показано: {len(tasks)} из {total_tasks}   ·   "
            f"Выполнено: {completed}"
        )

        self.refresh_compact_summary()
        self.refresh_calendar_marks()

    # =====================================
    # КОМПАКТНЫЙ ВИД
    # =====================================

    def clear_compact_tasks(self):
        while self.compact_task_layout.count():
            item = self.compact_task_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def refresh_compact_tasks(self):
        self.clear_compact_tasks()
        start_at, end_at = get_period_bounds("Сегодня")
        tasks = get_tasks(start_at, end_at)
        pending = [task for task in tasks if task["completed_at"] is None]
        self.compact_count_label.setText(str(len(pending)))

        if not pending:
            empty = QFrame()
            empty.setObjectName("compactEmpty")
            empty_box = QVBoxLayout(empty)
            empty_box.setContentsMargins(14, 18, 14, 18)
            empty_title = QLabel("На сегодня всё готово")
            empty_title.setObjectName("compactEmptyTitle")
            empty_hint = QLabel("Можно спокойно планировать следующий день")
            empty_hint.setObjectName("mutedLabel")
            empty_hint.setWordWrap(True)
            empty_box.addWidget(empty_title)
            empty_box.addWidget(empty_hint)
            self.compact_task_layout.addWidget(empty, 0, 0, 1, 2)

        for task_index, task in enumerate(pending):
            row = QFrame()
            row.setObjectName("compactTask")
            row_box = QHBoxLayout(row)
            row_box.setContentsMargins(12, 9, 10, 9)
            row_box.setSpacing(10)
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox.setToolTip("Отметить выполненной")
            checkbox.toggled.connect(
                lambda checked, task_id=task["id"], due_at=task["instance_due_at"]:
                self.toggle_completion(task_id, due_at, checked)
            )
            info = QVBoxLayout()
            info.setSpacing(2)
            title = QLabel(task["title"])
            title.setObjectName("compactTaskTitle")
            title.setWordWrap(True)
            due = datetime.strptime(task["due_at"], "%Y-%m-%d %H:%M:%S")
            meta = QLabel(f"{due:%H:%M}  ·  {task['organization_name']}")
            meta.setObjectName("mutedLabel")
            meta.setWordWrap(True)
            info.addWidget(title)
            info.addWidget(meta)
            row_box.addWidget(checkbox)
            row_box.addLayout(info, 1)
            self.compact_task_layout.addWidget(row, task_index // 2, task_index % 2)

    def refresh_compact_summary(self):
        count_today, count_overdue, next_task = (
            get_dashboard_stats()
        )

        self.date_label.setText(
            date.today().strftime("%d.%m.%Y")
        )

        self.summary_label.setText(
            str(count_today)
        )

        self.overdue_label.setText(
            str(count_overdue)
        )

        if next_task:
            due = datetime.strptime(
                next_task["due_at"],
                "%Y-%m-%d %H:%M:%S"
            )

            self.next_task_label.setText(
                f"Далее  ·  {due:%d.%m в %H:%M}  ·  {next_task['title']}"
            )
        else:
            self.next_task_label.setText(
                "Ближайших задач нет"
            )

        self.refresh_compact_tasks()

    # =====================================
    # АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ
    # =====================================

    def periodic_update(self):
        """Выполняется каждую минуту."""

        try:
            if self.expanded:
                self.refresh_task_area()
            else:
                self.refresh_compact_summary()

            self.notification_service.check_reminders()

        except (sqlite3.Error, ValueError) as error:
            print(
                f"Ошибка обновления виджета: {error}"
            )

    # =====================================
    # РЕЖИМЫ ОКНА
    # =====================================

    def toggle_expanded(self):
        if self.expanded:
            self.expanded_size = self.size()
            self.set_compact_mode()
        else:
            self.compact_size = self.size()
            self.set_expanded_mode()

    def set_compact_mode(self):
        self.expanded = False

        self.expanded_panel.hide()
        self.compact_panel.show()

        self.refresh_compact_summary()

        self.setMinimumSize(400, 420)
        self.resize(self.compact_size)

        self.title_bar.toggle_button.setText(
            "Планировщик"
        )

    def set_expanded_mode(self):
        self.expanded = True

        self.compact_panel.hide()
        self.expanded_panel.show()

        self.refresh_task_area()

        self.setMinimumSize(
            520,
            800 if self.current_period == "Календарь" else 600,
        )
        self.resize(self.expanded_size)

        self.title_bar.toggle_button.setText(
            "Виджет"
        )

    # =====================================
    # СИСТЕМНЫЙ ТРЕЙ
    # =====================================

    def create_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )

        self.setWindowIcon(icon)

        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip(
            "Бухгалтер — планировщик"
        )

        menu = QMenu()

        show_action = QAction(
            "Открыть планировщик",
            self
        )
        show_action.triggered.connect(
            self.restore_from_tray
        )

        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(
            self.quit_application
        )

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)

        self.tray.activated.connect(
            self.on_tray_activated
        )
        self.tray.show()

    def hide_to_tray(self):
        if self.tray is not None:
            self.hide()
        else:
            self.close()

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if (
            reason ==
            QSystemTrayIcon.ActivationReason.DoubleClick
        ):
            self.restore_from_tray()

    def quit_application(self):
        self.quitting = True
        self.refresh_timer.stop()
        if self.tray is not None:
            self.tray.hide()
        self.close()
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.tray is not None and not self.quitting:
            event.ignore()
            self.hide()
        else:
            event.accept()

    # =====================================
    # СТИЛИ
    # =====================================

    def apply_styles(self):
        self.setStyleSheet(STYLESHEET)
    def nativeEvent(self, event_type, message):
        # Let Windows resize the frameless window from all four edges/corners.
        import sys
        if sys.platform == "win32":
            import ctypes
            from ctypes.wintypes import MSG
            msg = MSG.from_address(int(message))
            if msg.message == 0x0084 and not self.isMaximized():  # WM_NCHITTEST
                from PySide6.QtCore import QPoint
                x = ctypes.c_short(msg.lParam & 0xffff).value
                y = ctypes.c_short((msg.lParam >> 16) & 0xffff).value
                pos = self.mapFromGlobal(QPoint(x, y))
                if self.rect().contains(pos):
                    left, right = pos.x() < 7, pos.x() >= self.width() - 7
                    top, bottom = pos.y() < 7, pos.y() >= self.height() - 7
                    hit = (13 if left else 14 if right else 12) if top else (
                        (16 if left else 17 if right else 15) if bottom else
                        10 if left else 11 if right else None)
                    if hit is not None:
                        return True, hit
        return super().nativeEvent(event_type, message)


"""Custom calendar grid with QCalendarWidget API compatibility."""

from PySide6.QtCore import QDate, QLocale, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCalendarWidget, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QTableView, QVBoxLayout, QWidget

from ui.dropdown import ComboBox


class PlannerCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLocale(QLocale("ru_RU"))
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setNavigationBarVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setMinimumSize(350, 340)
        self._marks = {}
        self._day_buttons = []
        for table in self.findChildren(QTableView):
            table.hide()
        panel = QWidget(self)
        panel.setObjectName("customCalendar")
        root = QVBoxLayout(panel)
        root.setContentsMargins(10, 10, 10, 9)
        root.setSpacing(7)
        header = QHBoxLayout()
        header.setSpacing(6)
        previous = self._arrow("‹", "Предыдущий месяц")
        following = self._arrow("›", "Следующий месяц")
        previous.clicked.connect(self.showPreviousMonth)
        following.clicked.connect(self.showNextMonth)
        self.month_select = ComboBox()
        self.month_select.setObjectName("calendarSelect")
        for month in range(1, 13):
            self.month_select.addItem(self.locale().standaloneMonthName(month).capitalize(), month)
        self.year_select = ComboBox()
        self.year_select.setObjectName("calendarYearSelect")
        for year in range(2000, 2101):
            self.year_select.addItem(str(year), year)
        self.month_select.setMinimumWidth(135)
        self.year_select.setFixedWidth(160)
        today = QPushButton("Сегодня")
        today.setObjectName("calendarToday")
        today.clicked.connect(self.select_today)
        header.addWidget(previous)
        header.addWidget(self.month_select, 1)
        header.addWidget(self.year_select)
        header.addWidget(today)
        header.addWidget(following)
        root.addLayout(header)
        weekdays = QHBoxLayout()
        weekdays.setSpacing(3)
        for index, text in enumerate(("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")):
            label = QLabel(text)
            label.setObjectName("calendarWeekend" if index >= 5 else "calendarWeekday")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            weekdays.addWidget(label, 1)
        root.addLayout(weekdays)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(3)
        for row in range(6):
            for column in range(7):
                button = QPushButton()
                button.setObjectName("calendarDay")
                button.setCheckable(True)
                button.setMinimumSize(34, 31)
                button.clicked.connect(lambda _checked=False, target=button: self._choose_day(target))
                grid.addWidget(button, row, column)
                self._day_buttons.append(button)
        root.addLayout(grid, 1)
        footer = QFrame()
        footer.setObjectName("calendarFooter")
        footer_row = QHBoxLayout(footer)
        footer_row.setContentsMargins(8, 7, 8, 0)
        caption = QLabel("Выбранная дата")
        caption.setObjectName("calendarSelectedCaption")
        self.selected_label = QLabel()
        self.selected_label.setObjectName("calendarSelectedDate")
        footer_row.addWidget(caption)
        footer_row.addStretch()
        footer_row.addWidget(self.selected_label)
        root.addWidget(footer)
        self.layout().addWidget(panel)
        self.month_select.currentIndexChanged.connect(self._jump_to_page)
        self.year_select.currentIndexChanged.connect(self._jump_to_page)
        self.currentPageChanged.connect(self._sync_page)
        self.selectionChanged.connect(self._render)
        self._sync_page()

    def _arrow(self, text, tooltip):
        button = QPushButton(text)
        button.setObjectName("calendarArrow")
        button.setFixedSize(34, 34)
        button.setToolTip(tooltip)
        return button

    def _jump_to_page(self, *_):
        month, year = self.month_select.currentData(), self.year_select.currentData()
        if month and year:
            self.setCurrentPage(year, month)

    def _sync_page(self, *_):
        self.month_select.blockSignals(True)
        self.year_select.blockSignals(True)
        self.month_select.setCurrentIndex(self.month_select.findData(self.monthShown()))
        year_index = self.year_select.findData(self.yearShown())
        if year_index < 0:
            self.year_select.addItem(str(self.yearShown()), self.yearShown())
            year_index = self.year_select.count() - 1
        self.year_select.setCurrentIndex(year_index)
        self.month_select.blockSignals(False)
        self.year_select.blockSignals(False)
        self._render()

    def _render(self):
        first = QDate(self.yearShown(), self.monthShown(), 1)
        start = first.addDays(-(first.dayOfWeek() - 1))
        selected, today = self.selectedDate(), QDate.currentDate()
        for offset, button in enumerate(self._day_buttons):
            day = start.addDays(offset)
            button.setText(str(day.day()))
            button.setProperty("dateValue", day)
            button.setProperty("outside", day.month() != self.monthShown())
            button.setProperty("today", day == today)
            button.setProperty("weekend", day.dayOfWeek() >= 6)
            button.setProperty("marked", day.toJulianDay() in self._marks)
            button.setChecked(day == selected)
            button.style().unpolish(button)
            button.style().polish(button)
        self.selected_label.setText(self.locale().toString(selected, "d MMMM yyyy"))

    def _choose_day(self, button):
        day = button.property("dateValue")
        if not isinstance(day, QDate):
            return
        self.setSelectedDate(day)
        if (day.year(), day.month()) != (self.yearShown(), self.monthShown()):
            self.setCurrentPage(day.year(), day.month())
        self._render()

    def select_today(self):
        today = QDate.currentDate()
        self.setSelectedDate(today)
        self.setCurrentPage(today.year(), today.month())

    def setDateTextFormat(self, day, text_format):
        super().setDateTextFormat(day, text_format)
        brush = text_format.background()
        if brush.style() == Qt.BrushStyle.NoBrush:
            self._marks.pop(day.toJulianDay(), None)
        else:
            color = brush.color() if brush.color().isValid() else QColor("#5577da")
            self._marks[day.toJulianDay()] = color.name()
        self._render()

    def wheelEvent(self, event):
        self.showPreviousMonth() if event.angleDelta().y() > 0 else self.showNextMonth()
        event.accept()

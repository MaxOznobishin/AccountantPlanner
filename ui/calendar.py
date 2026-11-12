"""Calendar with a stable navigation bar and readable date cells."""

from PySide6.QtCore import QDate, QLocale, QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)

from ui.dropdown import ComboBox


class PlannerCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLocale(QLocale("ru_RU"))
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.setGridVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.setNavigationBarVisible(False)
        self.setMinimumHeight(330)

        bar = QWidget(self)
        bar.setObjectName("calendarHeader")
        row = QHBoxLayout(bar)
        row.setContentsMargins(10, 9, 10, 7)
        row.setSpacing(6)
        previous = QPushButton("‹")
        following = QPushButton("›")
        for button, tip in ((previous, "Предыдущий месяц"), (following, "Следующий месяц")):
            button.setObjectName("calendarArrow")
            button.setFixedSize(34, 34)
            button.setToolTip(tip)

        self.month_combo = ComboBox()
        self.month_combo.setObjectName("calendarMonthCombo")
        self.month_combo.setMinimumWidth(135)
        for month in range(1, 13):
            name = self.locale().standaloneMonthName(month).capitalize()
            self.month_combo.addItem(name, month)

        self.year_input = QSpinBox()
        self.year_input.setObjectName("calendarYear")
        self.year_input.setRange(1900, 2200)
        self.year_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.year_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.year_input.setFixedWidth(74)

        today = QPushButton("Сегодня")
        today.setObjectName("calendarToday")
        previous.clicked.connect(self.showPreviousMonth)
        following.clicked.connect(self.showNextMonth)
        today.clicked.connect(self.select_today)
        row.addWidget(previous)
        row.addWidget(self.month_combo, 1)
        row.addWidget(self.year_input)
        row.addWidget(today)
        row.addWidget(following)
        self.layout().insertWidget(0, bar)

        footer = QWidget(self)
        footer.setObjectName("calendarFooter")
        footer_row = QHBoxLayout(footer)
        footer_row.setContentsMargins(12, 6, 12, 10)
        selected_caption = QLabel("Выбрано")
        selected_caption.setObjectName("calendarSelectedCaption")
        self.selected_label = QLabel()
        self.selected_label.setObjectName("calendarSelectedDate")
        footer_row.addWidget(selected_caption)
        footer_row.addStretch()
        footer_row.addWidget(self.selected_label)
        self.layout().addWidget(footer)

        self.month_combo.currentIndexChanged.connect(self.select_page)
        self.year_input.valueChanged.connect(self.select_page)
        self.currentPageChanged.connect(self.sync_navigation)
        self.selectionChanged.connect(self.update_selected_label)
        self.sync_navigation()
        self.update_selected_label()

    def sync_navigation(self, *_):
        self.month_combo.blockSignals(True)
        self.year_input.blockSignals(True)
        self.month_combo.setCurrentIndex(self.monthShown() - 1)
        self.year_input.setValue(self.yearShown())
        self.month_combo.blockSignals(False)
        self.year_input.blockSignals(False)

    def select_page(self, *_):
        self.setCurrentPage(
            self.year_input.value(),
            self.month_combo.currentData() or 1,
        )

    def update_selected_label(self):
        text = self.locale().toString(self.selectedDate(), "d MMMM yyyy")
        self.selected_label.setText(text)

    def select_today(self):
        self.setSelectedDate(QDate.currentDate())
        self.showSelectedDate()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.showPreviousMonth()
        elif event.angleDelta().y() < 0:
            self.showNextMonth()
        event.accept()

    def paintCell(self, painter, rect, day):
        painter.save()
        painter.fillRect(rect, QColor("#ffffff"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = day == self.selectedDate()
        today = day == QDate.currentDate()
        marked = self.dateTextFormat(day).background()
        side = min(rect.width() - 6, rect.height() - 4, 36)
        cell = QRectF(rect.center().x() - side / 2, rect.center().y() - side / 2, side, side)
        painter.setPen(Qt.PenStyle.NoPen)
        if selected or today:
            painter.setBrush(QColor("#5577da" if selected else "#e9eefb"))
            painter.drawRoundedRect(cell, 8, 8)
        weekend = day.dayOfWeek() in (Qt.DayOfWeek.Saturday, Qt.DayOfWeek.Sunday)
        color = ("#ffffff" if selected else "#4969c7" if today else
                 "#c34f58" if weekend else "#273247")
        if day.month() != self.monthShown() and not selected:
            color = "#a2acbc"
        painter.setPen(QColor(color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(day.day()))
        if marked.style() != Qt.BrushStyle.NoBrush:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#ffffff") if selected else marked.color())
            painter.drawEllipse(QRectF(rect.center().x() - 2, cell.bottom() - 5, 4, 4))
        painter.restore()

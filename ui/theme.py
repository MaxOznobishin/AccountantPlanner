"""Shared visual style for the planner and its dialogs."""

from pathlib import Path

STYLESHEET = """
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #24334b; }
QWidget#central, QDialog { background: #f3f6fb; }
QWidget#taskContent, QScrollArea { background: transparent; border: none; }
QFrame#titleBar { background: #ffffff; border-bottom: 1px solid #e1e7ef; }
QLabel#windowTitle { color: #246bce; font-size: 16px; font-weight: 700; }
QLabel#sectionTitle { font-size: 27px; font-weight: 700; color: #172b49; }
QLabel#hintLabel, QLabel#taskDetails, QLabel#dateLabel { color: #64748b; }
QLabel#summaryLabel { font-size: 22px; font-weight: 700; }
QLabel#overdueLabel { color: #c04444; }
QLabel#emptyState { color: #64748b; font-size: 15px; padding: 25px; }
QFrame#taskFrame { background: white; border: 1px solid #e0e7f0; border-radius: 12px; }
QFrame#taskFrame[state="overdue"] { border-left: 4px solid #df7373; }
QFrame#taskFrame[state="done"] { border-left: 4px solid #4fa58a; background: #f8fcfa; }
QLabel#statusBadge { color: #2864b8; font-size: 12px; }
QLabel#statusBadge[state="overdue"] { color: #bd4141; }
QLabel#statusBadge[state="done"] { color: #258363; }
QPushButton { background: #e8eef7; border: 1px solid transparent; border-radius: 7px; padding: 9px 13px; font-weight: 600; }
QPushButton:hover { background: #dbe6f6; }
QPushButton:pressed { background: #ccdafa; }
QPushButton:checked, QPushButton#newTaskButton, QPushButton#primaryButton { background: #286bd5; color: white; }
QPushButton#newTaskButton:hover, QPushButton#primaryButton:hover { background: #1e56b0; }
QPushButton#dangerButton { color: #b94343; background: #fff0f0; }
QPushButton:disabled { color: #9ba8b8; background: #edf0f5; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QDateTimeEdit:focus { border: 1px solid #4587e7; }
QLineEdit, QComboBox, QDateTimeEdit, QPlainTextEdit { background: white; border: 1px solid #d6dfeb; border-radius: 7px; padding: 9px; selection-background-color: #286bd5; }
QComboBox QAbstractItemView { background: white; color: #24334b; selection-background-color: #e3edfc; selection-color: #174d9b; padding: 5px; }
QComboBox, QDateTimeEdit { min-height: 20px; padding: 8px 38px 8px 12px; }
QComboBox::drop-down, QDateTimeEdit::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 32px; border: none; background: transparent; }
QComboBox::down-arrow, QDateTimeEdit::down-arrow { image: url("__CHEVRON__"); width: 16px; height: 16px; }
QComboBox { combobox-popup: 0; }
QComboBox:on { border-color: #4587e7; }
QComboBox QAbstractItemView { border: 1px solid #d6dfeb; outline: none; }
QComboBox QAbstractItemView::item { min-height: 30px; padding: 3px 10px; }
QListView#comboPopup { background: white; border: 1px solid #d6dfeb; border-radius: 6px; padding: 4px; outline: 0; }
QListView#comboPopup::item { min-height: 34px; padding: 0 10px; border: none; border-radius: 4px; color: #24334b; }
QListView#comboPopup::item:hover { background: #f0f5fd; }
QListView#comboPopup::item:selected { background: #e3edfc; color: #174d9b; }
QPushButton#closeAppButton { padding: 0; font-size: 22px; font-weight: 400; background: transparent; }
QPushButton#closeAppButton:hover { background: #df4545; color: white; }
QCheckBox { spacing: 10px; font-size: 15px; font-weight: 600; padding: 3px 0; }
QCheckBox::indicator { width: 18px; height: 18px; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #c5d0e0; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QCalendarWidget { background: white; border: 1px solid #d6dfeb; border-radius: 8px; }
QCalendarWidget QWidget { alternate-background-color: #f3f6fb; }
QCalendarWidget QToolButton { background: #e8eef7; color: #24334b; padding: 7px; border-radius: 5px; }
QCalendarWidget QAbstractItemView { background: white; color: #24334b; selection-background-color: #286bd5; selection-color: white; }
QCalendarWidget QWidget#calendarHeader { background: white; border: none; }
QLabel#calendarMonth { font-size: 16px; font-weight: 600; }
QPushButton#calendarArrow { padding: 0; font-size: 22px; background: #edf3fc; }
QPushButton#calendarToday { padding: 6px 12px; color: #246bce; background: #edf3fc; }
QCalendarWidget QAbstractItemView { border: none; outline: none; alternate-background-color: white; font-size: 13px; }
QTableWidget { background: white; alternate-background-color: #f6f9fd; border: 1px solid #dce4ef; border-radius: 8px; gridline-color: #edf1f7; selection-background-color: #e0ecfc; selection-color: #174d9b; }
QHeaderView::section { background: #eaf0f8; color: #52637d; border: none; padding: 12px; font-weight: 600; }
QMenu { background: white; border: 1px solid #d6dfeb; padding: 6px; }
QMenu::item { padding: 8px 20px; }
QMenu::item:selected { background: #e0ecfc; }
"""

STYLESHEET = STYLESHEET.replace("__CHEVRON__", (Path(__file__).parent / "assets" / "chevron-down.svg").as_posix())

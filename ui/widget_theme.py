"""Compact desktop-widget theme."""

from resources import resource_path

_ASSETS = resource_path("ui/assets")

STYLESHEET = """
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #e9edf5; }
QWidget#central, QDialog { background: #171b24; }
QWidget#central { border: 1px solid #2b3240; border-radius: 13px; }
QWidget#compactPanel, QWidget#compactTaskContent, QWidget#taskContent, QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QFrame#titleBar { background: #171b24; border-bottom: 1px solid #292f3d; }
QLabel#windowTitle { color: #8ea7ff; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
QPushButton#modeButton { background: transparent; color: #aeb8cb; padding: 7px 10px; font-weight: 500; }
QPushButton#modeButton:hover { color: white; background: #252b38; }
QPushButton#windowButton, QPushButton#closeAppButton { padding: 0; font-size: 20px; font-weight: 400; background: transparent; color: #8d98ab; }
QPushButton#windowButton:hover { background: #252b38; color: white; }
QPushButton#closeAppButton:hover { background: #df555d; color: white; }
QLabel#compactTitle { font-size: 24px; font-weight: 700; color: white; }
QLabel#dateLabel, QLabel#mutedLabel, QLabel#taskDetails, QLabel#hintLabel { color: #8d98ab; }
QLabel#statNumber { font-size: 23px; font-weight: 700; color: white; }
QFrame#statCard, QFrame#overdueCard { background: #222833; border: 1px solid #2f3746; border-radius: 12px; }
QFrame#overdueCard QLabel#statNumber { color: #ff858c; }
QFrame#compactTask { background: #202631; border: 1px solid #2b3341; border-radius: 10px; }
QFrame#compactTask:hover { background: #252c39; border-color: #3a4558; }
QLabel#compactTaskTitle { color: #f3f5f9; font-size: 14px; font-weight: 600; }
QFrame#compactEmpty { background: #202631; border: 1px dashed #394355; border-radius: 10px; }
QLabel#compactEmptyTitle { font-size: 15px; font-weight: 600; color: #dfe5ef; }
QLabel#nextTaskLabel { color: #aeb8cb; background: #1d222c; border-radius: 8px; padding: 9px 11px; }
QPushButton#quickAddButton { background: #7895ff; color: #10141c; border-radius: 12px; padding: 0; font-size: 26px; font-weight: 400; }
QPushButton#quickAddButton:hover { background: #93aaff; }
QLabel#sectionTitle { font-size: 24px; font-weight: 700; color: white; }
QLabel#emptyState { color: #8d98ab; font-size: 14px; padding: 24px; }
QFrame#taskFrame { background: #202631; border: 1px solid #2d3544; border-radius: 11px; }
QFrame#taskFrame[state="overdue"] { border-left: 3px solid #ef6a73; }
QFrame#taskFrame[state="done"] { border-left: 3px solid #55b99a; }
QLabel#statusBadge { color: #8ea7ff; font-size: 12px; }
QLabel#statusBadge[state="overdue"] { color: #ff858c; }
QLabel#statusBadge[state="done"] { color: #68cbaa; }
QPushButton { background: #2a3140; color: #e7ebf2; border: 1px solid transparent; border-radius: 8px; padding: 8px 12px; font-weight: 600; }
QPushButton:hover { background: #353e50; }
QPushButton:pressed { background: #404b60; }
QPushButton:checked, QPushButton#newTaskButton, QPushButton#primaryButton { background: #7895ff; color: #11151e; }
QPushButton#newTaskButton:hover, QPushButton#primaryButton:hover { background: #91a8ff; }
QPushButton#dangerButton { color: #ff9399; background: #38262d; }
QPushButton:disabled { color: #677184; background: #222733; }
QLineEdit, QComboBox, QDateTimeEdit, QPlainTextEdit { background: #202631; color: #e9edf5; border: 1px solid #343d4e; border-radius: 8px; padding: 9px; selection-background-color: #7895ff; selection-color: #11151e; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QDateTimeEdit:focus { border: 1px solid #7895ff; }
QComboBox, QDateTimeEdit { min-height: 20px; padding: 8px 38px 8px 12px; }
QComboBox::drop-down, QDateTimeEdit::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 34px; border: none; background: transparent; }
QComboBox::down-arrow, QDateTimeEdit::down-arrow { image: url("__CHEVRON__"); width: 16px; height: 16px; }
QComboBox { combobox-popup: 0; }
QListView#comboPopup { background: #202631; border: 1px solid #3a4456; border-radius: 7px; padding: 4px; outline: 0; }
QListView#comboPopup::item { min-height: 34px; padding: 0 10px; border: none; border-radius: 5px; color: #e9edf5; }
QListView#comboPopup::item:hover { background: #2d3544; }
QListView#comboPopup::item:selected { background: #7895ff; color: #11151e; }
QCheckBox { spacing: 9px; color: #f0f2f7; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #59657a; border-radius: 5px; background: #171b24; }
QCheckBox::indicator:hover { border-color: #8ea7ff; }
QCheckBox::indicator:checked { background: #7895ff; border-color: #7895ff; image: url("__CHECK__"); }
QScrollBar:vertical { background: transparent; width: 7px; margin: 0; }
QScrollBar::handle:vertical { background: #465064; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QCalendarWidget { background: #202631; border: 1px solid #343d4e; border-radius: 10px; }
QCalendarWidget QWidget#calendarHeader { background: #202631; border: none; }
QLabel#calendarMonth { font-size: 16px; font-weight: 600; color: white; }
QPushButton#calendarArrow { padding: 0; font-size: 22px; background: #2b3341; }
QPushButton#calendarToday { padding: 6px 12px; color: #9bb0ff; background: #2b3341; }
QCalendarWidget QAbstractItemView { background: #202631; color: #e9edf5; border: none; outline: none; alternate-background-color: #202631; font-size: 13px; }
QTableWidget { background: #202631; alternate-background-color: #242b37; border: 1px solid #343d4e; border-radius: 8px; gridline-color: #303847; selection-background-color: #3b4b75; selection-color: white; }
QHeaderView::section { background: #29303d; color: #aeb8cb; border: none; padding: 11px; font-weight: 600; }
QMenu { background: #202631; color: #e9edf5; border: 1px solid #3a4456; padding: 5px; }
QMenu::item { padding: 8px 20px; }
QMenu::item:selected { background: #30394a; }
"""

STYLESHEET = (STYLESHEET
              .replace("__CHEVRON__", (_ASSETS / "chevron-down.svg").as_posix())
              .replace("__CHECK__", (_ASSETS / "check.svg").as_posix()))

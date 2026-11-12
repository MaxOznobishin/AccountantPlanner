"""Light theme for the planner widget and dialogs."""

from resources import resource_path

_ASSETS = resource_path("ui/assets")

STYLESHEET = """
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #273247; }
QWidget#central, QDialog { background: #f4f6fa; }
QWidget#central { border: 1px solid #dfe4ec; border-radius: 13px; }
QWidget#compactPanel, QWidget#compactTaskContent, QWidget#taskContent, QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QFrame#titleBar { background: #ffffff; border-bottom: 1px solid #e7eaf0; }
QLabel#windowTitle { color: #4e6fcf; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
QPushButton#modeButton { background: transparent; color: #657187; padding: 7px 10px; font-weight: 500; }
QPushButton#modeButton:hover, QPushButton#windowButton:hover { color: #273247; background: #edf1f7; }
QPushButton#windowButton, QPushButton#closeAppButton { padding: 0; font-size: 20px; font-weight: 400; background: transparent; color: #7c879a; }
QPushButton#closeAppButton:hover { background: #e95961; color: white; }
QLabel#compactTitle { font-size: 24px; font-weight: 700; color: #202a3b; }
QLabel#dateLabel, QLabel#mutedLabel, QLabel#taskDetails, QLabel#hintLabel { color: #7b879b; }
QLabel#statNumber { font-size: 23px; font-weight: 700; color: #273247; }
QFrame#statCard, QFrame#overdueCard { background: #ffffff; border: 1px solid #e0e5ed; border-radius: 12px; }
QFrame#overdueCard QLabel#statNumber { color: #d94f58; }
QFrame#compactTask, QFrame#organizationCard { background: #ffffff; border: 1px solid #e0e5ed; border-radius: 10px; }
QFrame#compactTask:hover, QFrame#organizationCard:hover { background: #fbfcfe; border-color: #cbd4e3; }
QLabel#compactTaskTitle, QLabel#organizationName { color: #273247; font-size: 14px; font-weight: 600; }
QFrame#compactEmpty, QFrame#organizationEmpty { background: #ffffff; border: 1px dashed #ccd4e0; border-radius: 10px; }
QLabel#compactEmptyTitle { font-size: 15px; font-weight: 600; color: #374258; }
QLabel#nextTaskLabel { color: #657187; background: #eaeef5; border-radius: 8px; padding: 9px 11px; }
QPushButton#quickAddButton { background: #5577da; color: white; border-radius: 12px; padding: 0; font-size: 26px; font-weight: 400; }
QPushButton#quickAddButton:hover { background: #4667c8; }
QLabel#sectionTitle { font-size: 24px; font-weight: 700; color: #202a3b; }
QLabel#dialogSubtitle, QLabel#organizationCount { color: #7b879b; }
QLabel#emptyState { color: #7b879b; font-size: 14px; padding: 24px; }
QFrame#taskFrame { background: #ffffff; border: 1px solid #dfe5ed; border-radius: 11px; }
QFrame#taskFrame[state="overdue"] { border-left: 3px solid #e06269; }
QFrame#taskFrame[state="done"] { border-left: 3px solid #45a483; }
QLabel#statusBadge { color: #5577da; font-size: 12px; }
QLabel#statusBadge[state="overdue"] { color: #d94f58; }
QLabel#statusBadge[state="done"] { color: #328668; }
QPushButton { background: #e9edf4; color: #334057; border: 1px solid transparent; border-radius: 8px; padding: 8px 12px; font-weight: 600; }
QPushButton:hover { background: #dfe5ef; }
QPushButton:pressed { background: #d3dbe8; }
QPushButton:checked, QPushButton#newTaskButton, QPushButton#primaryButton { background: #5577da; color: white; }
QPushButton#newTaskButton:hover, QPushButton#primaryButton:hover { background: #4667c8; }
QPushButton#dangerButton { color: #c94c55; background: #fff0f1; }
QPushButton#cardActionButton { background: transparent; color: #536078; padding: 7px 9px; }
QPushButton#cardActionButton:hover { background: #edf1f7; }
QPushButton:disabled { color: #9aa4b4; background: #eceff4; }
QLineEdit, QComboBox, QDateTimeEdit, QPlainTextEdit { background: #ffffff; color: #273247; border: 1px solid #d7dde7; border-radius: 8px; padding: 9px; selection-background-color: #5577da; selection-color: white; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QDateTimeEdit:focus { border: 1px solid #6484df; }
QComboBox, QDateTimeEdit { min-height: 20px; padding: 8px 38px 8px 12px; }
QComboBox::drop-down, QDateTimeEdit::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 34px; border: none; background: transparent; }
QComboBox::down-arrow, QDateTimeEdit::down-arrow { image: url("__CHEVRON__"); width: 16px; height: 16px; }
QComboBox, QComboBox:focus { combobox-popup: 0; padding: 8px 36px 8px 12px; min-height: 20px; border: none; border-radius: 11px; background: #eaeef5; }
QComboBox:hover { background: #e1e7f1; }
QLabel#dropdownEmpty { color: #7b879b; padding: 12px; }
QListView#comboPopup { background: #ffffff; border: 1px solid #d7dde7; border-radius: 7px; padding: 4px; outline: 0; }
QListView#comboPopup::item { min-height: 34px; padding: 0 10px; border: none; border-radius: 5px; color: #273247; }
QListView#comboPopup::item:hover { background: #edf2fb; }
QListView#comboPopup::item:selected { background: #dfe8ff; color: #294baf; }
QFrame#selectPopup { background: transparent; border: none; }
QFrame#dropdownSurface { background: white; border: none; border-radius: 14px; }
QLineEdit#dropdownSearch, QLineEdit#dropdownSearch:focus { background: #f1f4f8; border: none; border-radius: 9px; padding: 9px 12px; }
QListWidget#selectPopupList { background: white; border: none; outline: none; padding: 0; }
QListWidget#selectPopupList::item { color: #273247; border-radius: 6px; padding: 0 10px; }
QListWidget#selectPopupList::item:hover { background: #eef2f8; }
QListWidget#selectPopupList::item:selected { background: #e1e9fc; color: #3155b5; }
QCheckBox { spacing: 9px; color: #273247; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #aeb8c8; border-radius: 5px; background: white; }
QCheckBox::indicator:hover { border-color: #6484df; }
QCheckBox::indicator:checked { background: #5577da; border-color: #5577da; image: url("__CHECK__"); }
QScrollBar:vertical { background: transparent; width: 7px; margin: 0; }
QScrollBar::handle:vertical { background: #c6ceda; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QCalendarWidget { background: white; border: 1px solid #d7dde7; border-radius: 10px; }
QCalendarWidget QWidget#calendarHeader { background: white; border: none; }
QPushButton#calendarArrow { padding: 0; font-size: 22px; background: #edf1f7; }
QPushButton#calendarToday { padding: 6px 12px; color: #4969c7; background: #edf1f7; }
QComboBox#calendarMonthCombo, QSpinBox#calendarYear { background: white; border: 1px solid #d7dde7; border-radius: 7px; padding: 7px 10px; font-size: 14px; font-weight: 600; }
QComboBox#calendarMonthCombo { padding-right: 32px; }
QWidget#calendarFooter { background: white; border: none; border-top: 1px solid #edf0f4; }
QLabel#calendarSelectedCaption { color: #8a95a7; font-size: 12px; }
QLabel#calendarSelectedDate { color: #34415a; font-weight: 600; }
QCalendarWidget QAbstractItemView { background: white; color: #273247; border: none; outline: none; alternate-background-color: white; font-size: 13px; }
QWidget#customCalendar { background: white; border: none; }
QComboBox#calendarSelect, QComboBox#calendarYearSelect { background: #eef1f7; border: none; border-radius: 11px; font-weight: 600; }
QComboBox#calendarSelect:hover, QComboBox#calendarYearSelect:hover { background: #e1e7f1; }
QLabel#calendarWeekday, QLabel#calendarWeekend { color: #8792a5; font-size: 11px; font-weight: 600; padding: 3px; }
QLabel#calendarWeekend { color: #cf6269; }
QPushButton#calendarDay { background: transparent; color: #334057; border: 1px solid transparent; border-radius: 8px; padding: 3px; font-weight: 500; }
QPushButton#calendarDay:hover { background: #eef2f8; }
QPushButton#calendarDay[outside="true"] { color: #b5bdc9; }
QPushButton#calendarDay[weekend="true"] { color: #c85b63; }
QPushButton#calendarDay[today="true"] { border: 1px solid #5577da; color: #3e61c4; font-weight: 700; }
QPushButton#calendarDay[marked="true"] { border-bottom: 3px solid #58a88b; }
QPushButton#calendarDay:checked { background: #5577da; color: white; border: 1px solid #5577da; font-weight: 700; }
QMenu { background: white; color: #273247; border: 1px solid #d7dde7; padding: 5px; }
QMenu::item { padding: 8px 20px; }
QMenu::item:selected { background: #edf2fb; }
"""

STYLESHEET = (STYLESHEET
              .replace("__CHEVRON__", (_ASSETS / "chevron-down.svg").as_posix())
              .replace("__CHECK__", (_ASSETS / "check-light.svg").as_posix()))

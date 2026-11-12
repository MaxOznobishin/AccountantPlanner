import sqlite3
from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime
from ui.calendar_v2 import PlannerCalendar
from ui.dropdown import ComboBox as QComboBox

from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from database.db import (
    add_task,
    get_organizations,
    update_task,
)


class TaskForm(QDialog):
    """Форма создания и редактирования задачи."""

    def __init__(
            self,
            parent=None,
            task=None,
            initial_organization_id=None
    ):
        super().__init__(parent)

        self.task = task

        if task:
            self.setWindowTitle("Редактировать задачу")
        else:
            self.setWindowTitle("Новая задача")

        self.setMinimumWidth(540)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        heading = QLabel(self.windowTitle())
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)
        form = QFormLayout()
        form.setSpacing(14)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        # Организация
        self.org_combo = QComboBox()

        for organization in get_organizations():
            self.org_combo.addItem(
                organization["name"],
                organization["id"]
            )

        # Название задачи
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText(
            "Например, подготовить платёжное поручение"
        )

        # Описание
        self.description_input = QPlainTextEdit()
        self.description_input.setPlaceholderText(
            "Дополнительная информация о задаче"
        )
        self.description_input.setMaximumHeight(90)

        # Дата и время выполнения
        self.due_input = QDateTimeEdit()
        self.due_input.setCalendarPopup(True)
        self.due_input.setCalendarWidget(PlannerCalendar())
        self.due_input.setDisplayFormat(
            "dd.MM.yyyy HH:mm"
        )

        default_due = (
                datetime.now().replace(
                    second=0,
                    microsecond=0
                ) + timedelta(hours=1)
        )

        self.due_input.setDateTime(
            QDateTime.fromString(
                default_due.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "yyyy-MM-dd HH:mm:ss"
            )
        )

        # Приоритет
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("Низкий", 1)
        self.priority_combo.addItem("Обычный", 2)
        self.priority_combo.addItem("Высокий", 3)
        self.priority_combo.setCurrentIndex(1)


        # Повторение задачи
        self.recurrence_combo = QComboBox()

        self.recurrence_combo.addItem(
            "Не повторять", "none"
        )
        self.recurrence_combo.addItem(
            "Каждый день", "daily"
        )
        self.recurrence_combo.addItem(
            "Каждую неделю", "weekly"
        )
        self.recurrence_combo.addItem(
            "Каждый месяц", "monthly"
        )
        self.recurrence_combo.addItem(
            "Каждый квартал", "quarterly"
        )
        self.recurrence_combo.addItem(
            "Каждый год", "yearly"
        )


        form.addRow("Организация:", self.org_combo)
        form.addRow("Название:", self.title_input)
        form.addRow("Описание:", self.description_input)
        form.addRow("Срок:", self.due_input)
        form.addRow("Приоритет:", self.priority_combo)
        form.addRow("Повторение:", self.recurrence_combo)

        layout.addLayout(form)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Сохранить")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("primaryButton")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")

        layout.addWidget(buttons)
        self.title_input.setFocus()

        # Предварительно выбранная организация
        if task:
            selected_id = task["organization_id"]
        else:
            selected_id = initial_organization_id

        if selected_id is not None:
            index = self.org_combo.findData(selected_id)

            if index >= 0:
                self.org_combo.setCurrentIndex(index)

        # Если редактируем существующую задачу
        if task:
            self.title_input.setText(task["title"])

            self.description_input.setPlainText(
                task["description"]
            )

            self.due_input.setDateTime(
                QDateTime.fromString(
                    task["due_at"],
                    "yyyy-MM-dd HH:mm:ss"
                )
            )

            index = self.priority_combo.findData(
                task["priority"]
            )

            if index >= 0:
                self.priority_combo.setCurrentIndex(index)


            recurrence_index = (
                self.recurrence_combo.findData(
                    task["recurrence"]
                )
            )

            if recurrence_index >= 0:
                self.recurrence_combo.setCurrentIndex(
                    recurrence_index
                )



    def save(self):
        """Сохранение задачи с правилом повторения."""

        organization_id = self.org_combo.currentData()

        title = self.title_input.text()
        description = (
            self.description_input.toPlainText()
        )

        due_at = self.due_input.dateTime().toString(
            "yyyy-MM-dd HH:mm:ss"
        )

        priority = self.priority_combo.currentData()

        recurrence = (
            self.recurrence_combo.currentData()
        )

        try:
            if self.task:
                update_task(
                    self.task["id"],
                    organization_id,
                    title,
                    description,
                    due_at,
                    priority,
                    recurrence
                )
            else:
                add_task(
                    organization_id,
                    title,
                    description,
                    due_at,
                    priority,
                    recurrence
                )

        except (ValueError, sqlite3.Error) as error:
            QMessageBox.warning(
                self,
                "Ошибка сохранения задачи",
                str(error)
            )
            return

        self.accept()


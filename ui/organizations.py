
import sqlite3
from ui.dropdown import ComboBox as PlannerComboBox

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.db import (
    add_organization,
    delete_organization,
    get_organizations,
    update_organization,
)


COLORS = {
    "Синий": "#3b82f6",
    "Зелёный": "#10b981",
    "Оранжевый": "#f59e0b",
    "Красный": "#ef4444",
    "Фиолетовый": "#a855f7",
    "Серый": "#64748b",
}


class OrganizationForm(QDialog):
    """Форма создания или редактирования организации."""

    def __init__(self, parent=None, organization=None):
        super().__init__(parent)

        self.organization = organization

        self.setWindowTitle(
            "Редактировать организацию"
            if organization else "Добавить организацию"
        )
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        form = QFormLayout()
        form.setSpacing(14)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ООО Альфа")

        self.inn_input = QLineEdit()
        self.inn_input.setPlaceholderText("10 или 12 цифр")
        self.inn_input.setMaxLength(12)

        self.color_input = PlannerComboBox()
        for color_name, hex_color in COLORS.items():
            self.color_input.addItem(color_name, hex_color)

        form.addRow("Название:", self.name_input)
        form.addRow("ИНН:", self.inn_input)
        form.addRow("Цвет:", self.color_input)

        layout.addLayout(form)

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

        if organization:
            self.name_input.setText(organization["name"])
            self.inn_input.setText(organization["inn"])

            index = self.color_input.findData(
                organization["color"]
            )
            if index >= 0:
                self.color_input.setCurrentIndex(index)

    def save(self):
        name = self.name_input.text().strip()
        inn = self.inn_input.text().strip()
        color = self.color_input.currentData()

        try:
            if self.organization:
                update_organization(
                    self.organization["id"],
                    name, inn, color
                )
            else:
                add_organization(name, inn, color)

        except (ValueError, sqlite3.Error) as error:
            QMessageBox.warning(
                self, "Ошибка сохранения", str(error)
            )
            return

        self.accept()


class OrganizationsDialog(QDialog):
    """Searchable card list for organization management."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Управление организациями")
        self.resize(680, 560)
        self.setMinimumSize(560, 440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        heading = QLabel("Организации")
        heading.setObjectName("sectionTitle")
        subtitle = QLabel("Контрагенты, для которых вы ведёте задачи")
        subtitle.setObjectName("dialogSubtitle")
        titles.addWidget(heading)
        titles.addWidget(subtitle)
        add_button = QPushButton("+ Добавить")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_new)
        header.addLayout(titles)
        header.addStretch()
        header.addWidget(add_button)
        layout.addLayout(header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по названию или ИНН")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.refresh_cards)
        self.count_label = QLabel()
        self.count_label.setObjectName("organizationCount")
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.count_label)
        layout.addLayout(search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.card_content = QWidget()
        self.card_layout = QVBoxLayout(self.card_content)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(8)
        scroll.setWidget(self.card_content)
        layout.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        close_button = QPushButton("Готово")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)

        self.organizations = []
        self.refresh_cards(reload=True)

    def clear_cards(self):
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def refresh_cards(self, *_args, reload=False):
        if reload or not self.organizations:
            self.organizations = get_organizations()
        self.clear_cards()
        query = self.search_input.text().strip().casefold()
        visible = [org for org in self.organizations if not query or query in
                   f"{org['name']} {org['inn']}".casefold()]
        self.count_label.setText(f"{len(visible)} из {len(self.organizations)}")

        if not visible:
            empty = QFrame()
            empty.setObjectName("organizationEmpty")
            box = QVBoxLayout(empty)
            box.setContentsMargins(20, 24, 20, 24)
            title = QLabel("Организации не найдены" if self.organizations else
                           "Добавьте первую организацию")
            title.setObjectName("compactEmptyTitle")
            hint = QLabel("Измените запрос поиска" if self.organizations else
                          "После этого можно будет создавать задачи")
            hint.setObjectName("mutedLabel")
            box.addWidget(title)
            box.addWidget(hint)
            self.card_layout.addWidget(empty)

        for org in visible:
            card = QFrame()
            card.setObjectName("organizationCard")
            row = QHBoxLayout(card)
            row.setContentsMargins(14, 12, 12, 12)
            row.setSpacing(12)
            color = QLabel()
            color.setFixedSize(12, 38)
            color.setStyleSheet(
                f"background: {org['color']}; border-radius: 6px;"
            )
            info = QVBoxLayout()
            info.setSpacing(3)
            name = QLabel(org["name"])
            name.setObjectName("organizationName")
            inn = QLabel(f"ИНН  {org['inn']}")
            inn.setObjectName("mutedLabel")
            info.addWidget(name)
            info.addWidget(inn)
            edit = QPushButton("Изменить")
            edit.setObjectName("cardActionButton")
            edit.clicked.connect(lambda _=False, item=org: self.edit_organization(item))
            delete = QPushButton("Удалить")
            delete.setObjectName("dangerButton")
            delete.clicked.connect(lambda _=False, item=org: self.delete_organization(item))
            row.addWidget(color)
            row.addLayout(info, 1)
            row.addWidget(edit)
            row.addWidget(delete)
            self.card_layout.addWidget(card)

        self.card_layout.addStretch()

    def add_new(self):
        dialog = OrganizationForm(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_cards(reload=True)

    def edit_organization(self, org):
        dialog = OrganizationForm(self, org)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_cards(reload=True)

    def delete_organization(self, org):
        answer = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить организацию «{org['name']}»?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_organization(org["id"])
        except (ValueError, sqlite3.Error) as error:
            QMessageBox.warning(
                self, "Ошибка удаления", str(error)
            )
            return

        self.refresh_cards(reload=True)

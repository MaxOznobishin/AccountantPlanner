"""Consistent dropdown lists without native menu decorations."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QListView, QStyledItemDelegate


class ComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        view = QListView(self)
        view.setObjectName("comboPopup")
        view.setItemDelegate(QStyledItemDelegate(view))
        view.setUniformItemSizes(True)
        view.setSpacing(2)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setView(view)
        self.setMaxVisibleItems(8)
        self.setMinimumContentsLength(12)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)

    def showPopup(self):
        popup = self.view().window()
        popup.setObjectName("comboPopupContainer")
        popup.setStyleSheet("QFrame#comboPopupContainer { background: white; border: 1px solid #d7dde7; }")
        super().showPopup()

"""Application combo box with a fully custom popup."""

from PySide6.QtCore import QEvent, QPoint, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QStyledItemDelegate, QStyle


class OptionDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        selected = bool(index.data(Qt.ItemDataRole.UserRole + 1))
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        focused = bool(option.state & QStyle.StateFlag.State_Selected)
        rect = option.rect.adjusted(2, 2, -2, -2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e8edfc" if selected else "#f0f3f8" if hovered or focused else "#ffffff"))
        painter.drawRoundedRect(QRectF(rect), 9, 9)
        painter.setPen(QColor("#3c5eb5" if selected else "#344057"))
        text_rect = rect.adjusted(12, 0, -32, 0)
        text = option.fontMetrics.elidedText(index.data(), Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, text)
        if selected:
            x, y = rect.right() - 18, rect.center().y()
            painter.setPen(QPen(QColor("#5577da"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(x - 4, y, x - 1, y + 3)
            painter.drawLine(x - 1, y + 3, x + 5, y - 3)
        painter.restore()


class ComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup = None
        self._opening = False
        self.setMaxVisibleItems(8)
        self.setMinimumHeight(38)

    def showPopup(self):
        self.hidePopup()
        if not self.count():
            return
        popup = QFrame(self.window(), Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        popup.setObjectName("selectPopup")
        popup.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        popup.setStyleSheet("QFrame#selectPopup { background: transparent; border: none; }")
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(0, 0, 0, 0)
        surface = QFrame()
        surface.setObjectName("dropdownSurface")
        layout.addWidget(surface)
        layout = QVBoxLayout(surface)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)
        search = QLineEdit()
        search.setObjectName("dropdownSearch")
        search.setPlaceholderText("Поиск…")
        search.setClearButtonEnabled(True)
        search.setVisible(self.count() > 8)
        layout.addWidget(search)
        list_widget = QListWidget()
        list_widget.setObjectName("selectPopupList")
        list_widget.setMouseTracking(True)
        list_widget.viewport().setMouseTracking(True)
        list_widget.setItemDelegate(OptionDelegate(list_widget))
        list_widget.setFrameShape(QFrame.Shape.NoFrame)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        for index in range(self.count()):
            item = QListWidgetItem(self.itemIcon(index), self.itemText(index))
            item.setData(Qt.ItemDataRole.UserRole + 1, index == self.currentIndex())
            item.setSizeHint(QSize(0, 40))
            item.setToolTip(self.itemText(index))
            item.setData(Qt.ItemDataRole.UserRole, index)
            list_widget.addItem(item)
        list_widget.setCurrentRow(self.currentIndex())
        list_widget.itemClicked.connect(self._select_item)
        list_widget.installEventFilter(self)
        search.installEventFilter(self)
        layout.addWidget(list_widget)
        empty = QLabel("Ничего не найдено")
        empty.setObjectName("dropdownEmpty")
        empty.hide()
        layout.addWidget(empty)
        def filter_items(query):
            visible = []
            for row in range(list_widget.count()):
                item = list_widget.item(row)
                match = query.casefold() in self.itemText(row).casefold()
                item.setHidden(not match)
                if match:
                    visible.append(item)
            empty.setVisible(not visible)
            list_widget.setCurrentItem(visible[0] if visible else None)
        search.textChanged.connect(filter_items)
        search.setProperty("dropdownSearch", True)
        rows = min(self.count(), self.maxVisibleItems())
        popup.resize(max(self.width(), 180), rows * 40 + 12 + (44 if self.count() > 8 else 0))
        position = self.mapToGlobal(QPoint(0, self.height() + 5))
        screen = self.screen().availableGeometry()
        if position.y() + popup.height() > screen.bottom():
            position.setY(self.mapToGlobal(QPoint(0, -popup.height() - 4)).y())
        if position.x() + popup.width() > screen.right():
            position.setX(screen.right() - popup.width())
        popup.move(position)
        popup.destroyed.connect(lambda: self._clear_popup(popup))
        self._popup = popup
        QApplication.instance().installEventFilter(self)
        self._opening = True
        popup.show()
        (search if self.count() > 8 else list_widget).setFocus()
        if list_widget.currentItem() is not None:
            list_widget.scrollToItem(list_widget.currentItem())
        self._opening = False

    def _clear_popup(self, popup):
        if self._popup is popup:
            self._popup = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._popup is not None and self._popup.isVisible():
                self.hidePopup()
            else:
                self.showPopup()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def eventFilter(self, watched, event):
        if self._popup is not None and event.type() == QEvent.Type.MouseButtonPress:
            if not self._popup.geometry().contains(event.globalPosition().toPoint()) and not self.rect().contains(self.mapFromGlobal(event.globalPosition().toPoint())):
                self.hidePopup()
        if event.type() == QEvent.Type.KeyPress:
            view = self._popup.findChild(QListWidget) if self._popup else None
            if view is None:
                return super().eventFilter(watched, event)
            if isinstance(watched, QLineEdit) and event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                view.setFocus()
                return True
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                item = view.currentItem()
                if item is not None:
                    self._select_item(item)
                return True
            if event.key() == Qt.Key.Key_Escape:
                self.hidePopup()
                return True
        return super().eventFilter(watched, event)

    def _select_item(self, item):
        self.setCurrentIndex(item.data(Qt.ItemDataRole.UserRole))
        self.activated.emit(self.currentIndex())
        self.hidePopup()

    def hidePopup(self):
        if self._opening:
            return
        if self._popup is not None:
            QApplication.instance().removeEventFilter(self)
            popup, self._popup = self._popup, None
            popup.close()

    def wheelEvent(self, event):
        event.ignore()

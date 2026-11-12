"""Application update controls and worker lifetime management."""

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QMessageBox

from services.updater import UpdateWorker, install_update
from version import APP_VERSION


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Настройки приложения")
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        heading = QLabel("Обновление приложения")
        heading.setObjectName("compactEmptyTitle")
        layout.addWidget(heading)
        layout.addWidget(QLabel(f"Установлена версия {APP_VERSION}"))
        self.status_label = QLabel("Проверьте наличие новой версии.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.update_button = QPushButton("Обновить")
        self.update_button.setObjectName("primaryButton")
        self.update_button.clicked.connect(self.check_update)
        layout.addWidget(self.update_button)

    def check_update(self):
        if self.worker is not None and self.worker.isRunning():
            return
        self.update_button.setEnabled(False)
        self.status_label.setText("Проверяем обновления…")
        self.worker = UpdateWorker(self)
        self.worker.status.connect(self.status_label.setText)
        self.worker.error.connect(self.show_error)
        self.worker.no_update.connect(
            lambda: self.status_label.setText("Установлена последняя версия.")
        )
        self.worker.update_ready.connect(self.update_ready)
        self.worker.finished.connect(lambda: self.update_button.setEnabled(True))
        self.worker.start()

    def show_error(self, message):
        self.status_label.setText(f"Обновление не выполнено: {message}")

    def update_ready(self, version, filename):
        reply = QMessageBox.question(
            self, "Обновление готово",
            f"Версия {version} загружена и проверена. Установить и перезапустить приложение?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply != QMessageBox.StandardButton.Yes:
            self.status_label.setText("Установка отложена. Для установки нажмите «Обновить».")
            return
        try:
            install_update(filename)
        except Exception as error:
            self.show_error(str(error))
            return
        # The helper waits for the main process, including this worker, to exit.
        if self.worker is not None and self.worker.isRunning():
            self.worker.finished.connect(self.parent().quit_application)
        else:
            self.parent().quit_application()

    def reject(self):
        if self.worker is not None and self.worker.isRunning():
            self.status_label.setText("Дождитесь завершения проверки и загрузки обновления.")
            return
        super().reject()

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            event.ignore()
            return
        super().closeEvent(event)

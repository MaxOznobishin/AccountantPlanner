
import sys

from PySide6.QtWidgets import QApplication

from database.db import init_database
from ui.widget import AccountantWidget


def main():
    # Подготавливаем локальную базу SQLite
    init_database()

    # Запускаем графическое приложение
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Бухгалтер — планировщик")

    widget = AccountantWidget()

    app.setQuitOnLastWindowClosed(widget.tray is None)

    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

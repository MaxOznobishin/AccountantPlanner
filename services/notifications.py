
import sqlite3
from datetime import datetime

from PySide6.QtWidgets import QSystemTrayIcon

from database.db import (
    get_upcoming_reminders,
    mark_notification_sent,
)


class NotificationService:
    """Сервис напоминаний о сроках задач."""

    def __init__(self, tray):
        self.tray = tray

    def check_reminders(self):
        """
        Проверяет сроки и показывает
        уведомления через системный трей.
        """

        if self.tray is None:
            return

        if not self.tray.isVisible():
            return

        try:
            reminders = get_upcoming_reminders(60)

        except (sqlite3.Error, ValueError) as error:
            print(
                f"Ошибка проверки уведомлений: {error}"
            )
            return

        if not reminders:
            return

        if len(reminders) == 1:
            task = reminders[0]

            due = datetime.strptime(
                task["due_at"],
                "%Y-%m-%d %H:%M:%S"
            )

            title = "Напоминание о задаче"

            message = (
                f"{task['title']}\n"
                f"Организация: "
                f"{task['organization_name']}\n"
                f"Срок: {due:%d.%m.%Y %H:%M}"
            )

        else:
            title = (
                f"Приближаются сроки: "
                f"{len(reminders)} задач"
            )

            lines = []

            for task in reminders[:3]:
                due = datetime.strptime(
                    task["due_at"],
                    "%Y-%m-%d %H:%M:%S"
                )

                lines.append(
                    f"{due:%H:%M} — "
                    f"{task['title']} "
                    f"({task['organization_name']})"
                )

            if len(reminders) > 3:
                lines.append(
                    f"И ещё {len(reminders) - 3} задач"
                )

            message = "\n".join(lines)

        try:
            self.tray.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                10000
            )

            for task in reminders:
                mark_notification_sent(
                    task["id"],
                    task["instance_due_at"]
                )

        except sqlite3.Error as error:
            print(
                f"Ошибка сохранения уведомления: {error}"
            )

        except Exception as error:
            print(
                f"Ошибка отображения уведомления: {error}"
            )

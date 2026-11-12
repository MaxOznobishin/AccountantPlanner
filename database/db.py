import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
import calendar

import os
import sys
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent

# Проверяем, запущен исходный Python-код или EXE.
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    local_app_data = Path(
        os.environ.get(
            "LOCALAPPDATA",
            str(Path.home() / "AppData" / "Local")
        )
    )

    DATA_DIR = (
        local_app_data
        / "AccountantPlanner"
        / "data"
    )
else:
    # В PyCharm пока оставляем прежний путь.
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "accountant.db"

# Перенос старой БД при переходе на EXE.
if IS_FROZEN and not DB_PATH.exists():
    old_db = (
        Path(sys.executable).resolve().parent
        / "data"
        / "accountant.db"
    )

    if old_db.is_file():
        shutil.copy2(old_db, DB_PATH)



@contextmanager
def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_database():
    """Создание таблиц при первом запуске."""

    with get_connection() as connection:
        connection.execute("""
                           CREATE TABLE IF NOT EXISTS organizations
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               name
                               TEXT
                               NOT
                               NULL,
                               inn
                               TEXT
                               NOT
                               NULL
                               DEFAULT
                               '',
                               color
                               TEXT
                               NOT
                               NULL
                               DEFAULT
                               '#3b82f6',
                               created_at
                               TEXT
                               NOT
                               NULL
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           """)

        connection.execute("""
                           CREATE TABLE IF NOT EXISTS tasks
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               organization_id
                               INTEGER
                               NOT
                               NULL,
                               title
                               TEXT
                               NOT
                               NULL,
                               description
                               TEXT
                               NOT
                               NULL
                               DEFAULT
                               '',
                               due_at
                               TEXT
                               NOT
                               NULL,
                               priority
                               INTEGER
                               NOT
                               NULL
                               DEFAULT
                               2
                               CHECK (
                               priority
                               IN
                           (
                               1,
                               2,
                               3
                           )),
                               completed_at TEXT,
                               created_at TEXT NOT NULL
                               DEFAULT CURRENT_TIMESTAMP,
                               FOREIGN KEY
                           (
                               organization_id
                           )
                               REFERENCES organizations
                           (
                               id
                           )
                               ON DELETE RESTRICT
                               )
                           """)

        connection.execute("""
                           CREATE INDEX IF NOT EXISTS idx_tasks_due_at
                               ON tasks(due_at)
                           """)

        connection.execute("""
                           CREATE INDEX IF NOT EXISTS idx_tasks_organization_due
                               ON tasks(organization_id, due_at)
                           """)

        # Обновление старой таблицы tasks
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(tasks)"
            ).fetchall()
        }

        if "recurrence" not in columns:
            connection.execute("""
                               ALTER TABLE tasks
                                   ADD COLUMN recurrence TEXT NOT NULL
                                       DEFAULT 'none'
                               """)

        # История выполнения повторяющихся задач
        connection.execute("""
                           CREATE TABLE IF NOT EXISTS task_occurrences
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               task_id
                               INTEGER
                               NOT
                               NULL,
                               occurrence_due_at
                               TEXT
                               NOT
                               NULL,
                               completed_at
                               TEXT
                               NOT
                               NULL,
                               UNIQUE
                           (
                               task_id,
                               occurrence_due_at
                           ),
                               FOREIGN KEY
                           (
                               task_id
                           )
                               REFERENCES tasks
                           (
                               id
                           )
                               ON DELETE CASCADE
                               )
                           """)

        connection.execute("""
                           CREATE INDEX IF NOT EXISTS
                               idx_occurrences_task_date
                               ON task_occurrences(
                               task_id,
                               occurrence_due_at
                               )
                           """)


        # История напоминаний по отдельным выполнениям
        connection.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                occurrence_due_at TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                sent_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(
                    task_id,
                    occurrence_due_at,
                    reminder_type
                ),

                FOREIGN KEY (task_id)
                    REFERENCES tasks(id)
                    ON DELETE CASCADE
            )
        """)



# ==========================================
# ОРГАНИЗАЦИИ
# ==========================================

def get_organizations():
    with get_connection() as connection:
        rows = connection.execute("""
                                  SELECT id, name, inn, color, created_at
                                  FROM organizations
                                  ORDER BY name COLLATE NOCASE, id
                                  """).fetchall()

        return [dict(row) for row in rows]


def validate_organization(name, inn):
    if not name:
        raise ValueError("Укажите название организации")

    if inn and (
            not inn.isdigit()
            or len(inn) not in (10, 12)
    ):
        raise ValueError(
            "ИНН должен содержать 10 или 12 цифр"
        )


def add_organization(name, inn="", color="#3b82f6"):
    name = name.strip()
    inn = inn.strip()

    validate_organization(name, inn)

    with get_connection() as connection:
        cursor = connection.execute("""
                                    INSERT INTO organizations (name, inn, color)
                                    VALUES (?, ?, ?)
                                    """, (name, inn, color))

        return cursor.lastrowid


def update_organization(
        org_id, name, inn="", color="#3b82f6"
):
    name = name.strip()
    inn = inn.strip()

    validate_organization(name, inn)

    with get_connection() as connection:
        cursor = connection.execute("""
                                    UPDATE organizations
                                    SET name  = ?,
                                        inn   = ?,
                                        color = ?
                                    WHERE id = ?
                                    """, (name, inn, color, org_id))

        if cursor.rowcount == 0:
            raise ValueError("Организация не найдена")


def delete_organization(org_id):
    with get_connection() as connection:
        cursor = connection.execute("""
                                    DELETE
                                    FROM organizations
                                    WHERE id = ?
                                    """, (org_id,))

        if cursor.rowcount == 0:
            raise ValueError("Организация не найдена")


# ==========================================
# ЗАДАЧИ
# ==========================================

def validate_task(organization_id, title, due_at, priority):
    if not isinstance(organization_id, int):
        raise ValueError("Выберите организацию")

    if not title.strip():
        raise ValueError("Введите название задачи")

    if priority not in (1, 2, 3):
        raise ValueError("Некорректный приоритет")

    try:
        datetime.strptime(due_at, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        raise ValueError(
            "Некорректная дата или время"
        ) from None



def add_task(
    organization_id,
    title,
    description,
    due_at,
    priority=2,
    recurrence="none"
):
    """Создаёт разовую или регулярную задачу."""

    title = title.strip()
    description = description.strip()

    validate_task(
        organization_id,
        title,
        due_at,
        priority
    )
    validate_recurrence(recurrence)

    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO tasks (
                organization_id,
                title,
                description,
                due_at,
                priority,
                recurrence
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            organization_id,
            title,
            description,
            due_at,
            priority,
            recurrence
        ))

        return cursor.lastrowid




def update_task(
    task_id,
    organization_id,
    title,
    description,
    due_at,
    priority,
    recurrence="none"
):
    """Изменяет задачу с сохранением истории."""

    title = title.strip()
    description = description.strip()

    validate_task(
        organization_id,
        title,
        due_at,
        priority
    )
    validate_recurrence(recurrence)

    with get_connection() as connection:
        old = connection.execute("""
            SELECT *
            FROM tasks
            WHERE id = ?
        """, (task_id,)).fetchone()

        if old is None:
            raise ValueError("Задача не найдена")

        history_count = connection.execute("""
            SELECT COUNT(*)
            FROM task_occurrences
            WHERE task_id = ?
        """, (task_id,)).fetchone()[0]

        schedule_changed = (
            old["due_at"] != due_at
            or old["recurrence"] != recurrence
        )

        # Пока запрещаем менять расписание,
        # если уже есть история регулярных выполнений.
        if history_count and schedule_changed:
            raise ValueError(
                "Нельзя изменить расписание задачи "
                "с историей выполнений. "
                "Название, организацию, описание "
                "и приоритет менять можно."
            )

        # Разовая выполненная задача, переводимая
        # в регулярную, сохраняет выполнение
        # первоначальной даты.
        old_completed = old["completed_at"]

        if (
            old["recurrence"] == "none"
            and recurrence != "none"
            and old_completed is not None
            and schedule_changed
            and old["due_at"] != due_at
        ):
            raise ValueError(
                "Сначала снимите отметку выполнения "
                "или оставьте первоначальный срок."
            )

        connection.execute("""
            UPDATE tasks
            SET organization_id = ?,
                title = ?,
                description = ?,
                due_at = ?,
                priority = ?,
                recurrence = ?
            WHERE id = ?
        """, (
            organization_id,
            title,
            description,
            due_at,
            priority,
            recurrence,
            task_id
        ))

        if (
            old["recurrence"] == "none"
            and recurrence != "none"
            and old_completed is not None
        ):
            connection.execute("""
                INSERT INTO task_occurrences (
                    task_id,
                    occurrence_due_at,
                    completed_at
                )
                VALUES (?, ?, ?)
            """, (
                task_id,
                old["due_at"],
                old_completed
            ))

            connection.execute("""
                UPDATE tasks
                SET completed_at = NULL
                WHERE id = ?
            """, (task_id,))

        if (
            old["recurrence"] != "none"
            and recurrence == "none"
        ):
            connection.execute("""
                UPDATE tasks
                SET completed_at = NULL
                WHERE id = ?
            """, (task_id,))



def delete_task(task_id):
    """Удаление задачи."""

    with get_connection() as connection:
        cursor = connection.execute("""
                                    DELETE
                                    FROM tasks
                                    WHERE id = ?
                                    """, (task_id,))

        if cursor.rowcount == 0:
            raise ValueError("Задача не найдена")



def set_task_completed(
    task_id,
    completed,
    occurrence_due_at=None
):
    """Отмечает конкретное выполнение задачи."""

    with get_connection() as connection:
        task = connection.execute("""
            SELECT id, due_at, recurrence
            FROM tasks
            WHERE id = ?
        """, (task_id,)).fetchone()

        if task is None:
            raise ValueError("Задача не найдена")

        recurrence = task["recurrence"]

        if recurrence == "none":
            completed_at = (
                datetime.now().strftime(DATETIME_FORMAT)
                if completed else None
            )

            connection.execute("""
                UPDATE tasks
                SET completed_at = ?
                WHERE id = ?
            """, (completed_at, task_id))

            return

        if not occurrence_due_at:
            raise ValueError(
                "Не указана дата регулярной задачи"
            )

        if not is_valid_occurrence(
            task["due_at"],
            recurrence,
            occurrence_due_at
        ):
            raise ValueError(
                "Дата не соответствует расписанию"
            )

        if completed:
            completed_at = datetime.now().strftime(
                DATETIME_FORMAT
            )

            connection.execute("""
                INSERT INTO task_occurrences (
                    task_id,
                    occurrence_due_at,
                    completed_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(
                    task_id, occurrence_due_at
                )
                DO UPDATE SET
                    completed_at = excluded.completed_at
            """, (
                task_id,
                occurrence_due_at,
                completed_at
            ))

        else:
            connection.execute("""
                DELETE FROM task_occurrences
                WHERE task_id = ?
                  AND occurrence_due_at = ?
            """, (task_id, occurrence_due_at))



def get_task(task_id):
    """Получение одной задачи по ID."""

    with get_connection() as connection:
        row = connection.execute("""
                                 SELECT *
                                 FROM tasks
                                 WHERE id = ?
                                 """, (task_id,)).fetchone()

        return dict(row) if row else None



def get_tasks(start_at, end_at, organization_id=None):
    """
    Возвращает задачи за период с рассчитанными
    датами регулярных повторений.
    """

    start = datetime.strptime(
        start_at, DATETIME_FORMAT
    )
    end = datetime.strptime(
        end_at, DATETIME_FORMAT
    )

    sql = """
        SELECT
            t.*,
            o.name AS organization_name,
            o.color AS organization_color
        FROM tasks AS t
        JOIN organizations AS o
            ON o.id = t.organization_id
        WHERE t.due_at < ?
    """

    params = [end_at]

    if organization_id is not None:
        sql += " AND t.organization_id = ?"
        params.append(organization_id)

    result = []

    with get_connection() as connection:
        tasks = connection.execute(
            sql, params
        ).fetchall()

        for task_row in tasks:
            task = dict(task_row)

            anchor = datetime.strptime(
                task["due_at"], DATETIME_FORMAT
            )

            recurrence = task["recurrence"]

            dates = occurrence_dates(
                anchor,
                recurrence,
                start,
                end
            )

            # История выполнений этой задачи
            if recurrence != "none":
                completed_rows = connection.execute("""
                    SELECT occurrence_due_at, completed_at
                    FROM task_occurrences
                    WHERE task_id = ?
                      AND occurrence_due_at >= ?
                      AND occurrence_due_at < ?
                """, (
                    task["id"], start_at, end_at
                )).fetchall()

                completed_map = {
                    row["occurrence_due_at"]:
                        row["completed_at"]
                    for row in completed_rows
                }
            else:
                completed_map = {}

            for occurrence in dates:
                item = task.copy()

                due_str = occurrence.strftime(
                    DATETIME_FORMAT
                )

                item["due_at"] = due_str
                item["instance_due_at"] = due_str
                item["series_due_at"] = task["due_at"]

                if recurrence != "none":
                    item["completed_at"] = (
                        completed_map.get(due_str)
                    )

                result.append(item)

    result.sort(
        key=lambda task: (
            task["due_at"],
            task["id"]
        )
    )

    return result



# ==========================================
# ПЕРИОДЫ
# ==========================================

def get_period_bounds(period, current_date=None):
    today = current_date or date.today()

    if period == "Сегодня":
        start = today
        end = today + timedelta(days=1)

    elif period == "Неделя":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)

    elif period == "Месяц":
        start = today.replace(day=1)

        if start.month == 12:
            end = date(start.year + 1, 1, 1)
        else:
            end = date(start.year, start.month + 1, 1)

    elif period == "Год":
        start = date(today.year, 1, 1)
        end = date(today.year + 1, 1, 1)

    else:
        raise ValueError("Неизвестный период")

    return (
        f"{start:%Y-%m-%d} 00:00:00",
        f"{end:%Y-%m-%d} 00:00:00"
    )


# ==========================================
# СТАТИСТИКА ВИДЖЕТА
# ==========================================


def get_dashboard_stats():
    """Статистика всех организаций для мини-виджета."""

    now = datetime.now()
    today_start = datetime.combine(
        now.date(),
        datetime.min.time()
    )
    tomorrow = today_start + timedelta(days=1)

    # Ищем будущие повторения на 3 года вперёд.
    future_limit = now + timedelta(days=3 * 366)

    count_today = 0
    count_overdue = 0
    next_task = None

    with get_connection() as connection:
        tasks = connection.execute("""
            SELECT id, title, due_at,
                   recurrence, completed_at
            FROM tasks
        """).fetchall()

        for task in tasks:
            anchor = datetime.strptime(
                task["due_at"],
                DATETIME_FORMAT
            )

            recurrence = task["recurrence"]

            if recurrence == "none":
                completed_dates = (
                    {task["due_at"]}
                    if task["completed_at"] else set()
                )
            else:
                rows = connection.execute("""
                    SELECT occurrence_due_at
                    FROM task_occurrences
                    WHERE task_id = ?
                """, (task["id"],)).fetchall()

                completed_dates = {
                    row["occurrence_due_at"]
                    for row in rows
                }

            # Исторические и сегодняшние выполнения
            if anchor < tomorrow:
                for occurrence in occurrence_dates(
                    anchor,
                    recurrence,
                    anchor,
                    tomorrow
                ):
                    due_str = occurrence.strftime(
                        DATETIME_FORMAT
                    )

                    if due_str in completed_dates:
                        continue

                    if today_start <= occurrence < tomorrow:
                        count_today += 1

                    if occurrence < now:
                        count_overdue += 1

            # Ближайшее будущее выполнение
            if recurrence == "none":
                candidates = occurrence_dates(
                    anchor,
                    recurrence,
                    now,
                    max(
                        future_limit,
                        anchor + timedelta(seconds=1)
                    )
                )
            else:
                candidates = occurrence_dates(
                    anchor,
                    recurrence,
                    now,
                    future_limit
                )

            for occurrence in candidates:
                due_str = occurrence.strftime(
                    DATETIME_FORMAT
                )

                if due_str in completed_dates:
                    continue

                if (
                    next_task is None
                    or occurrence < next_task["date"]
                ):
                    next_task = {
                        "title": task["title"],
                        "date": occurrence
                    }

                # Нашли ближайшее невыполненное
                # повторение именно этой серии
                break

    if next_task:
        next_task = {
            "title": next_task["title"],
            "due_at": next_task["date"].strftime(
                DATETIME_FORMAT
            )
        }

    return count_today, count_overdue, next_task



# ==========================================
# РЕГУЛЯРНЫЕ ЗАДАЧИ
# ==========================================

RECURRENCE_NAMES = {
    "none": "Разовая",
    "daily": "Ежедневная",
    "weekly": "Еженедельная",
    "monthly": "Ежемесячная",
    "quarterly": "Ежеквартальная",
    "yearly": "Ежегодная",
}

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def validate_recurrence(recurrence):
    if recurrence not in RECURRENCE_NAMES:
        raise ValueError("Неизвестный тип повторения")


def add_months(anchor, months):
    """
    Прибавляет месяцы относительно исходной даты.

    Например:
    31 января -> 28 февраля -> 31 марта.
    """
    month_index = (
            anchor.year * 12
            + anchor.month - 1
            + months
    )

    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1

    if not 1 <= year <= 9999:
        raise ValueError("Дата выходит за допустимый диапазон")

    day = min(
        anchor.day,
        calendar.monthrange(year, month)[1]
    )

    return anchor.replace(
        year=year,
        month=month,
        day=day
    )


def occurrence_dates(anchor, recurrence, start, end):
    """
    Возвращает даты задачи в полуоткрытом
    интервале [start, end).

    anchor - первоначальный срок задачи.
    """

    validate_recurrence(recurrence)

    if start >= end:
        return

    if recurrence == "none":
        if start <= anchor < end:
            yield anchor
        return

    if recurrence in ("daily", "weekly"):
        step = timedelta(
            days=1 if recurrence == "daily" else 7
        )

        if start <= anchor:
            current = anchor
        else:
            count = max(
                0,
                (start - anchor) // step
            )
            current = anchor + count * step

            if current < start:
                current += step

        while current < end:
            yield current
            current += step

        return

    step_months = {
        "monthly": 1,
        "quarterly": 3,
        "yearly": 12,
    }[recurrence]

    months_between = (
            (start.year - anchor.year) * 12
            + start.month - anchor.month
    )

    count = max(
        0,
        months_between // step_months
    )

    while True:
        current = add_months(
            anchor,
            count * step_months
        )

        if current >= end:
            break

        if current >= start and current >= anchor:
            yield current

        count += 1


def is_valid_occurrence(anchor_str, recurrence, due_str):
    """Проверяет принадлежность даты расписанию."""

    try:
        anchor = datetime.strptime(
            anchor_str, DATETIME_FORMAT
        )
        due = datetime.strptime(
            due_str, DATETIME_FORMAT
        )
    except (TypeError, ValueError):
        return False

    if due < anchor:
        return False

    return any(
        occurrence_dates(
            anchor,
            recurrence,
            due,
            due + timedelta(seconds=1)
        )
    )


# ==========================================
# УВЕДОМЛЕНИЯ
# ==========================================

def was_notification_sent(
    task_id,
    occurrence_due_at,
    reminder_type="one_hour"
):
    """Проверяет, отправляли ли напоминание."""

    with get_connection() as connection:
        row = connection.execute("""
            SELECT 1
            FROM notifications
            WHERE task_id = ?
              AND occurrence_due_at = ?
              AND reminder_type = ?
            LIMIT 1
        """, (
            task_id,
            occurrence_due_at,
            reminder_type
        )).fetchone()

        return row is not None


def mark_notification_sent(
    task_id,
    occurrence_due_at,
    reminder_type="one_hour"
):
    """Сохраняет факт отправки напоминания."""

    with get_connection() as connection:
        connection.execute("""
            INSERT OR IGNORE INTO notifications (
                task_id,
                occurrence_due_at,
                reminder_type
            )
            VALUES (?, ?, ?)
        """, (
            task_id,
            occurrence_due_at,
            reminder_type
        ))


def get_upcoming_reminders(minutes=60):
    """
    Возвращает невыполненные задачи,
    срок которых наступит в ближайшие N минут.
    """

    now = datetime.now()
    end = now + timedelta(minutes=minutes)

    tasks = get_tasks(
        now.strftime(DATETIME_FORMAT),
        (
            end + timedelta(seconds=1)
        ).strftime(DATETIME_FORMAT)
    )

    reminders = []

    for task in tasks:
        if task["completed_at"] is not None:
            continue

        due = datetime.strptime(
            task["due_at"],
            DATETIME_FORMAT
        )

        if not (now < due <= end):
            continue

        if was_notification_sent(
            task["id"],
            task["instance_due_at"]
        ):
            continue

        reminders.append(task)

    return reminders


import sys
from pathlib import Path


def resource_path(relative_path):
    """
    Возвращает путь к ресурсу.

    Работает:
    - в PyCharm;
    - в собранном EXE через PyInstaller.
    """

    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base_path = Path(__file__).resolve().parent

    relative_path = Path(relative_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Путь к ресурсу должен быть относительным")
    return base_path / relative_path

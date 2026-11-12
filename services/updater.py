
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from version import (
    APP_VERSION,
    GITHUB_OWNER,
    GITHUB_REPO,
    RELEASE_FILENAME,
)


def version_tuple(value):
    """Преобразует 1.2.3 в (1, 2, 3)."""
    value = value.lstrip("v")

    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError(
            f"Некорректная версия: {value}"
        )

    return tuple(map(int, value.split(".")))


def get_update_directory():
    base = Path(
        os.environ.get(
            "LOCALAPPDATA",
            tempfile.gettempdir()
        )
    )

    folder = base / "AccountantPlanner" / "updates"
    folder.mkdir(parents=True, exist_ok=True)

    return folder


class UpdateWorker(QThread):
    """Проверяет и скачивает обновление вне UI-потока."""

    status = Signal(str)
    update_ready = Signal(str, str)
    no_update = Signal()
    error = Signal(str)

    def run(self):
        try:
            if GITHUB_OWNER == "YOUR_USERNAME":
                raise RuntimeError(
                    "Укажите GITHUB_OWNER в version.py"
                )

            self.status.emit("Проверяем GitHub...")

            api_url = (
                f"https://api.github.com/repos/"
                f"{GITHUB_OWNER}/{GITHUB_REPO}"
                f"/releases/latest"
            )

            request = urllib.request.Request(
                api_url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "AccountantPlanner-Updater"
                }
            )

            import json

            with urllib.request.urlopen(
                request,
                timeout=20
            ) as response:
                release = json.load(response)

            latest_version = release["tag_name"]

            if (
                version_tuple(latest_version)
                <= version_tuple(APP_VERSION)
            ):
                self.no_update.emit()
                return

            if not (getattr(sys, "frozen", False) and sys.platform == "win32"):
                raise RuntimeError(
                    f"Доступна версия {latest_version}. Автоматическая установка "
                    "доступна в собранной Windows EXE-версии."
                )

            # Ищем именно EXE-файл.
            asset = next(
                (
                    item
                    for item in release.get("assets", [])
                    if item["name"] == RELEASE_FILENAME
                ),
                None
            )

            if asset is None:
                raise RuntimeError(
                    "В релизе отсутствует "
                    f"{RELEASE_FILENAME}"
                )

            digest = asset.get("digest") or ""

            if not re.fullmatch(
                r"sha256:[0-9a-fA-F]{64}",
                digest
            ):
                raise RuntimeError(
                    "У релиза отсутствует корректная "
                    "контрольная сумма SHA-256."
                )

            expected_hash = digest.split(":", 1)[1].lower()

            download_url = asset["browser_download_url"]

            # Не разрешаем произвольные внешние
            # адреса из ответа API.
            from urllib.parse import urlparse

            parsed = urlparse(download_url)

            expected_path = (
                f"/{GITHUB_OWNER}/{GITHUB_REPO}/"
                "releases/download/"
            )

            if (
                parsed.scheme != "https"
                or parsed.hostname != "github.com"
                or not parsed.path.lower().startswith(
                    expected_path.lower()
                )
            ):
                raise RuntimeError(
                    "Недопустимый адрес обновления."
                )

            self.status.emit(
                f"Скачиваем версию {latest_version}..."
            )

            update_dir = get_update_directory()
            target = update_dir / RELEASE_FILENAME
            temporary = update_dir / (
                RELEASE_FILENAME + ".part"
            )

            actual_hash = hashlib.sha256()

            try:
                download_request = urllib.request.Request(
                    download_url,
                    headers={
                        "User-Agent":
                            "AccountantPlanner-Updater"
                    }
                )

                with urllib.request.urlopen(
                    download_request,
                    timeout=60
                ) as response, open(
                    temporary, "wb"
                ) as file:
                    while True:
                        chunk = response.read(1024 * 1024)

                        if not chunk:
                            break

                        file.write(chunk)
                        actual_hash.update(chunk)

                if actual_hash.hexdigest() != expected_hash:
                    raise RuntimeError(
                        "Контрольная сумма файла не совпадает. "
                        "Обновление отменено."
                    )

                temporary.replace(target)

            finally:
                temporary.unlink(missing_ok=True)

            self.update_ready.emit(
                latest_version,
                str(target)
            )

        except Exception as exc:
            self.error.emit(str(exc))


# ==========================================
# ВНЕШНИЙ ОБНОВЛЯТОР WINDOWS
# ==========================================

UPDATER_SCRIPT = r"""
param(
    [string]$TargetExe,
    [string]$DownloadedExe,
    [int]$MainProcessId,
    [string]$LogFile
)

$ErrorActionPreference = "Stop"

try {
    # Ждём завершения основного приложения.
    Wait-Process -Id $MainProcessId `
        -Timeout 90 -ErrorAction SilentlyContinue

    $backup = "$TargetExe.old"

    # Повторяем попытки, если Windows
    # ещё удерживает файл.
    $updated = $false

    for ($i = 0; $i -lt 40; $i++) {
        try {
            if (Test-Path $backup) {
                Remove-Item $backup -Force
            }

            Move-Item $TargetExe $backup -Force

            try {
                Copy-Item $DownloadedExe $TargetExe
                $updated = $true
                break
            }
            catch {
                Move-Item $backup $TargetExe -Force
                throw
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    if (-not $updated) {
        throw "Не удалось заменить EXE-файл"
    }

    # Запускаем новую версию.
    Start-Process -FilePath $TargetExe
}
catch {
    $_ | Out-File $LogFile -Encoding UTF8

    # Если файл отсутствует, пробуем
    # восстановить предыдущую версию.
    if (-not (Test-Path $TargetExe)) {
        if (Test-Path "$TargetExe.old") {
            Move-Item "$TargetExe.old" $TargetExe -Force
        }
    }
}
"""


def install_update(downloaded_file):
    """Запускает внешний процесс установки."""

    if not (
        getattr(sys, "frozen", False)
        and sys.platform == "win32"
    ):
        raise RuntimeError(
            "Установка доступна только в Windows EXE."
        )

    executable = Path(sys.executable).resolve()
    downloaded = Path(downloaded_file).resolve()

    if not downloaded.is_file():
        raise FileNotFoundError(
            "Скачанный файл обновления не найден."
        )

    update_dir = get_update_directory()

    script_path = update_dir / "install_update.ps1"
    log_path = update_dir / "update_error.log"

    script_path.write_text(
        UPDATER_SCRIPT,
        encoding="utf-8-sig"
    )

    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-TargetExe",
            str(executable),
            "-DownloadedExe",
            str(downloaded),
            "-MainProcessId",
            str(os.getpid()),
            "-LogFile",
            str(log_path)
        ],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

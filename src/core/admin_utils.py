import ctypes
import os
import sys
from typing import NoReturn

from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt


def is_admin() -> bool:
    """Проверяет, запущен ли процесс с правами администратора Windows."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        print(
            "Warning: Could not determine admin status "
            "(ctypes.windll.shell32.IsUserAnAdmin not found). Assuming not admin."
        )
        return False


def show_critical_error(
    title_key: str, title_default: str, message: str, translator
) -> None:
    """
    Отображает критическое окно ошибки, которое остается поверх других окон.

    Args:
        title_key: Ключ для перевода заголовка окна.
        title_default: Заголовок окна по умолчанию.
        message: Текст сообщения об ошибке.
        translator: Экземпляр переводчика.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv if hasattr(sys, "argv") else [])

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(translator.translate(title_key, title_default))
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.setModal(True)
    msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    msg_box.exec()


def restart_as_admin(translator) -> NoReturn:
    """
    Пытается перезапустить текущий скрипт с правами администратора.
    Если успешно, текущий процесс завершается.
    Если неудачно, показывает окно ошибки и завершает текущий процесс.

    Args:
        translator: Экземпляр переводчика.
    """
    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
        executable = sys.executable
        full_params = f'"{script}" {params}'

        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, full_params, None, 1
        )

        if result <= 32:
            error_code_map = {
                0: "ERROR_OUTOFMEMORY",
                2: "ERROR_FILE_NOT_FOUND",
                3: "ERROR_PATH_NOT_FOUND",
                5: "SE_ERR_ACCESSDENIED",
                8: "SE_ERR_OOM",
                31: "SE_ERR_NOASSOC",
                32: "SE_ERR_DLLNOTFOUND",
            }
            error_name = error_code_map.get(result, f"Unknown error code {result}")

            error_message = translator.translate(
                "admin_restart_failed",
                "Failed to obtain administrator privileges. The application cannot continue.",
            )
            error_message += f"\nError code: {result} ({error_name})"

            if result == 5:
                error_message += f"\n({translator.translate('uac_denied', 'The user likely denied the UAC prompt.')})"

            show_critical_error(
                "admin_error", "Admin rights error", error_message, translator
            )
            sys.exit(1)
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        error_text = translator.translate(
            "admin_restart_error", "Failed to restart with admin rights"
        )
        show_critical_error(
            "admin_error",
            "Admin rights error",
            f"{error_text}:\nExecutable or script not found: {e}",
            translator,
        )
        sys.exit(1)
    except Exception as e:
        error_text = translator.translate(
            "admin_restart_error", "Failed to restart with admin rights"
        )
        show_critical_error(
            "admin_error", "Admin rights error", f"{error_text}:\n{e}", translator
        )
        sys.exit(1)

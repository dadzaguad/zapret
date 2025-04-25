import ctypes
import os
import sys
from PyQt6.QtWidgets import QMessageBox
from src.gui.translations import translator


def is_admin():
    """Проверяет, запущено ли приложение с правами администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def restart_as_admin():
    """Перезапускает текущее приложение с правами администратора."""
    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
    except Exception as e:
        QMessageBox.critical(
            None,
            translator.translate("admin_error", "Admin rights error"),
            f"{translator.translate('admin_restart_error', 'Failed to restart with admin rights')}:\n{e}",
        )
    sys.exit(1)

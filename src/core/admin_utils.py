import ctypes
import os
import sys
from PyQt6.QtWidgets import QMessageBox
from src.gui.translations import translator


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


def restart_as_admin():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        if result <= 32:

            QMessageBox.critical(
                None,
                translator.translate("admin_error", "Admin rights error"),
                f"{translator.translate('admin_restart_failed', 'Failed to obtain administrator privileges. The application cannot continue.')}\nError code: {result}",
            )
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        QMessageBox.critical(
            None,
            translator.translate("admin_error", "Admin rights error"),
            f"{translator.translate('admin_restart_error', 'Failed to restart with admin rights')}:\n{e}",
        )
        sys.exit(1)

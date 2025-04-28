import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.gui.gui import CommandRunnerApp
from src.core.admin_utils import is_admin, restart_as_admin
from src.scripts.commands import ZapretRunner
from src.gui.translations import translator

if __name__ == "__main__":

    if not is_admin():
        restart_as_admin()

    app = QApplication(sys.argv)

    try:
        zapret_runner_instance = ZapretRunner()

        window = CommandRunnerApp(zapret_runner=zapret_runner_instance)
        window.show()

        sys.exit(app.exec())

    except RuntimeError as e:
        QMessageBox.critical(
            None,
            translator.translate("initialization_error_title", "Initialization Error"),
            f"{translator.translate('initialization_error_message', 'Failed to initialize the application:')}\n{e}",
        )
        sys.exit(1)
    except Exception as e:

        QMessageBox.critical(
            None,
            translator.translate("critical_error_title", "Critical Error"),
            f"{translator.translate('unexpected_error_message', 'An unexpected error occurred:')}\n{e}",
        )
        sys.exit(1)

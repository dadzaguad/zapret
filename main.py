import sys
from PyQt6.QtWidgets import QApplication
from src.gui.gui import CommandRunnerApp
from src.core.admin_utils import is_admin, restart_as_admin

if __name__ == "__main__":
    if not is_admin():
        restart_as_admin()

    app = QApplication(sys.argv)
    window = CommandRunnerApp()
    window.show()
    sys.exit(app.exec())
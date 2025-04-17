import sys
# Импорт GUI
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.gui.gui import CommandRunnerApp
from src.core.admin_utils import is_admin, restart_as_admin

if __name__ == '__main__':
    # Проверка запуска с правами администратора
    if not is_admin():
        restart_as_admin()

    # Запуск приложения
    app = QApplication(sys.argv)
    window = CommandRunnerApp()
    window.show()
    sys.exit(app.exec())
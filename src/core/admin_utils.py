import ctypes
import os
import sys
from PyQt6.QtWidgets import QMessageBox

def is_admin():
    """Проверяет, запущено ли приложение с правами администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def restart_as_admin():
    """Перезапускает текущее приложение с правами администратора без вывода консоли."""
    try:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join(f'"{arg}"' for arg in sys.argv[1:])
        # Используем pythonw.exe для скрытия консоли
        pythonw_exe = sys.executable.replace('python.exe', 'pythonw.exe')  # Заменяем на pythonw.exe
        ctypes.windll.shell32.ShellExecuteW(None, "runas", pythonw_exe, f'"{script}" {params}', None, 1)
    except Exception as e:
        QMessageBox.critical(None, "Ошибка прав администратора",
                             f"Не удалось перезапустить программу с правами администратора:\n{e}")
    sys.exit(1)
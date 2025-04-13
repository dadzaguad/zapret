import os
import sys
import ctypes
import subprocess

class BatchFileManager:
    """
    Логический слой для работы с BAT-файлами и проверки административных прав.
    """

    def __init__(self, script_dir):
        """
        Инициализация с указанием папки, где будут находиться bat-файлы.
        """
        self.script_dir = script_dir

    def get_batch_files(self):
        """
        Возвращает список BAT-файлов из папки script_dir.
        """
        if not os.path.exists(self.script_dir):
            return None  # Папка не существует
        return [
            file for file in os.listdir(self.script_dir)
            if file.endswith(".bat") and not file.startswith("service")
        ]

    def run_batch_file(self, batch_file):
        """
        Запускает BAT-файл с правами администратора.
        """
        try:
            subprocess.run(
                f'powershell Start-Process cmd -ArgumentList \'/c "{batch_file}"\' -Verb runAs',
                check=True,
                shell=True
            )
            return True, f"Файл {batch_file} успешно запущен."
        except Exception as e:
            return False, f"Ошибка при запуске файла {batch_file}.\n{str(e)}"

    @staticmethod
    def is_user_admin():
        """
        Проверяет, запущен ли скрипт с правами администратора.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def relaunch_as_admin():
        """
        Перезапускает скрипт с правами администратора.
        """
        script_path = os.path.abspath(sys.argv[0])
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)
            sys.exit(0)
        except Exception as e:
            raise RuntimeError(f"Не удалось запросить права администратора: {e}")
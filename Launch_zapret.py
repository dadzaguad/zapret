import os
import sys
import ctypes
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class BatchFileLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zapret Discord")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #2c2f33;")

        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Выберите файл")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Путь к папке scripts
        script_dir = os.path.join(os.getcwd(), "scripts")

        # Проверяем, существует ли папка scripts
        if not os.path.exists(script_dir):
            no_files_label = QLabel("Папка 'scripts' не найдена.")
            no_files_label.setFont(QFont("Arial", 12))
            no_files_label.setStyleSheet("color: white;")
            no_files_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_files_label)
            return

        # Поиск .bat файлов в папке scripts
        batch_files = [
            file for file in os.listdir(script_dir)
            if file.endswith(".bat") and not file.startswith("service")
        ]

        if batch_files:
            for batch_file in batch_files:
                file_name_without_extension = os.path.splitext(batch_file)[0]
                button = QPushButton(file_name_without_extension)
                button.setFont(QFont("Arial", 12))
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #5865f2; 
                        color: white; 
                        border: #000000; 
                        padding: 10px; 
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                # Передаём полный путь к bat-файлу в обработчик нажатия
                button.clicked.connect(lambda checked, b=os.path.join(script_dir, batch_file): self.run_batch_file(b))
                layout.addWidget(button)
        else:
            no_files_label = QLabel("Файлы .bat в папке 'scripts' не найдены.")
            no_files_label.setFont(QFont("Arial", 12))
            no_files_label.setStyleSheet("color: white;")
            no_files_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_files_label)

        close_button = QPushButton("Закрыть")
        close_button.setFont(QFont("Arial", 12))
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #d9534f; 
                color: white; 
                border: none; 
                padding: 10px; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
        """)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def run_batch_file(self, batch_file):
        """Запуск BAT файла с правами администратора"""
        try:
            subprocess.run(
                f'powershell Start-Process cmd -ArgumentList \'/c "{batch_file}"\' -Verb runAs',
                check=True,
                shell=True
            )
            QMessageBox.information(self, "Успех", f"Файл {batch_file} успешно запущен.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Что-то пошло не так.\n{str(e)}")


def is_user_admin():
    """
    Проверяет, запущен ли скрипт с правами администратора.
    :return: True, если запущен от имени администратора, иначе False.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def relaunch_as_admin():
    """
    Перезапускает скрипт с правами администратора.
    """
    script_path = os.path.abspath(sys.argv[0])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, script_path, None, 1
        )
        sys.exit(0)
    except Exception as e:
        print(f"Не удалось запросить права администратора: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if not is_user_admin():
        relaunch_as_admin()

    app = QApplication([])
    window = BatchFileLauncher()
    window.show()
    app.exec()
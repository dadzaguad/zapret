import os
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from src.core.logic import BatchFileManager


class BatchFileLauncher(QWidget):
    def __init__(self, batch_manager):
        super().__init__()
        self.batch_manager = batch_manager
        self.init_ui()

    def init_ui(self):
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

        # Получаем список bat-файлов через объект бизнес-логики
        batch_files = self.batch_manager.get_batch_files()

        if batch_files is None:
            no_files_label =  QLabel("Не найдено bat-файлов в указанной директории.")
            no_files_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_files_label.setStyleSheet("color: red; font-size: 14px;")
            layout.addWidget(no_files_label)
        else:
            for file in batch_files:
                button = QPushButton(file)
                button.setStyleSheet(
                    "background-color: #7289da; color: white; font-size: 14px; padding: 10px;"
                )
                button.clicked.connect(lambda checked, f=file: self.launch_batch_file(f))
                layout.addWidget(button)

    def launch_batch_file(self, batch_file):
        # Проверка перед выполнением
        confirm = QMessageBox.question(
            self,
            "Подтвердите запуск",
            f"Вы действительно хотите выполнить {batch_file}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success = self.batch_manager.execute_batch_file(batch_file)
            if success:
                QMessageBox.information(self, "Успех", f"Файл {batch_file} выполнен успешно!")
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить {batch_file}.")
        else:
            QMessageBox.information(self, "Отмена", "Выполнение файла отменено.")


if __name__ == "__main__":
    # Бизнес-логика: создаем объект для обработки .bat файлов
    batch_manager = BatchFileManager(directory="bat_files")

    # Инициализация приложения
    app = QApplication(sys.argv)
    launcher = BatchFileLauncher(batch_manager)
    launcher.show()
    sys.exit(app.exec())
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox, QLabel,
    QScrollArea
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QCloseEvent

# Импорт вашего модуля команд
script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
if script_dir not in sys.path:
    sys.path.append(script_dir)

try:
    import commands
except ImportError as e:
    app_temp = QApplication.instance()
    if app_temp is None:
        app_temp = QApplication([sys.argv[0]] if sys.argv else [''])
    QMessageBox.critical(None, "Ошибка импорта",
                         f"Не удалось импортировать 'commands.py'.\n{e}")
    sys.exit(1)


class CommandWorker(QObject):
    command_started = pyqtSignal(str)
    process_stopped = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str) # message, command_name (None if stop error)
    finished = pyqtSignal()

    def __init__(self, command_name=None, process_name=None):
        super().__init__()
        self._command_name = command_name
        self._process_name = process_name

    def run_command(self):
        if not self._command_name:
            self.error_occurred.emit("Worker: Не указано имя команды.", self._command_name)
            self.finished.emit()
            return
        try:
            commands.run_zapret_command(self._command_name)
            self.command_started.emit(self._command_name)
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при запуске '{self._command_name}':\n{e}", self._command_name)
        finally:
            self.finished.emit()

    def stop_command(self):
        if not self._process_name:
            self.error_occurred.emit("Worker: Не указано имя процесса.", None)
            self.finished.emit()
            return
        try:
            success_flag = commands.stop_process(self._process_name)
            if success_flag:
                 self.process_stopped.emit(f"Попытка остановки '{self._process_name}' завершена.")
            else:
                 self.error_occurred.emit(f"Не удалось остановить '{self._process_name}'.\n(См. консоль)", None)
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при остановке '{self._process_name}':\n{e}", None)
        finally:
            self.finished.emit()

# --- Основной класс приложения ---
class CommandRunnerApp(QWidget):
    RUNNING_STYLE = "background-color: lightgreen; color: black;"
    DEFAULT_STYLE = "" # Пустая строка сбрасывает стиль к значению по умолчанию

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Менеджер')
        self.setGeometry(200, 200, 400, 400)
        self.main_layout = QVBoxLayout(self)
        self.active_threads = set()
        self.command_buttons = {}
        self.running_command_name = None

        # --- Кнопки команд ---
        cmd_buttons_widget = QWidget()
        cmd_layout = QVBoxLayout()
        cmd_buttons_widget.setLayout(cmd_layout)
        cmd_layout.addWidget(QLabel("Запуск профиля:"))

        for command_name in commands.COMMAND_ARGS.keys():
            button = QPushButton(command_name)
            button.clicked.connect(lambda checked, name=command_name: self.run_selected_command(name))
            cmd_layout.addWidget(button)
            self.command_buttons[command_name] = button

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cmd_buttons_widget)
        self.main_layout.addWidget(scroll)

        # --- Кнопка Остановки ---
        self.stop_button = QPushButton("Остановить winws")
        self.stop_button.setStyleSheet("background-color: #D00005;")
        self.stop_button.clicked.connect(self.stop_current_command)
        self.main_layout.addWidget(self.stop_button)

        # Устанавливаем начальное состояние UI
        self._set_ui_state_can_start()

    # --- Методы управления состоянием UI ---

    def _set_ui_state_can_start(self):
        """Состояние: Готово к запуску любой команды."""
        # Сбрасываем выделение предыдущей кнопки (если была)
        if self.running_command_name:
            button = self.command_buttons.get(self.running_command_name)
            if button:
                button.setStyleSheet(self.DEFAULT_STYLE)

        self.running_command_name = None # Сбрасываем имя запущенной команды
        # Включаем все кнопки команд
        for button in self.command_buttons.values():
            button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.stop_button.setStyleSheet("background-color: #5c0a0a;") # Возвращаем цвет

    def _set_ui_state_can_stop(self, command_name):
        """Состояние: Одна команда запущена, можно только остановить."""
        # Сбрасываем стиль старой кнопки, если вдруг что-то пошло не так
        if self.running_command_name and self.running_command_name != command_name:
             old_button = self.command_buttons.get(self.running_command_name)
             if old_button:
                 old_button.setStyleSheet(self.DEFAULT_STYLE)

        self.running_command_name = command_name # Устанавливаем имя запущенной команды
        # Выключаем все кнопки команд
        for btn_name, button in self.command_buttons.items():
            if btn_name == command_name:
                button.setEnabled(True) # Оставляем активной только запущенную
                button.setStyleSheet(self.RUNNING_STYLE) # Применяем стиль
            else:
                button.setEnabled(False) # Остальные выключаем
                button.setStyleSheet(self.DEFAULT_STYLE) # Сбрасываем стиль на всякий случай
        # Включаем кнопку Стоп
        self.stop_button.setEnabled(True)
        self.stop_button.setStyleSheet("background-color: #800000;") # Можно сделать ярче

    def _set_ui_state_busy(self, operation_type="start"):
        """Состояние: Выполняется операция (старт/стоп), все неактивно."""
        for button in self.command_buttons.values():
            button.setEnabled(False)
        self.stop_button.setEnabled(False)
        # Можно добавить label "Выполняется..."

    # --- Методы запуска/остановки ---

    def run_selected_command(self, command_name):
        """Запускает выбранную команду, если никакая другая не запущена."""
        if self.running_command_name is not None:
            # Эта проверка не должна срабатывать из-за управления состоянием кнопок,
            # но оставим на всякий случай
            QMessageBox.warning(self, "Запрещено",
                                f"Команда '{self.running_command_name}' уже выполняется.")
            return

        self._set_ui_state_busy("start") # Блокируем UI на время старта потока

        thread = QThread()
        worker = CommandWorker(command_name=command_name)
        worker.moveToThread(thread)
        self.active_threads.add(thread)
        thread.worker = worker

        thread.started.connect(worker.run_command)
        worker.command_started.connect(self.on_command_started)
        worker.error_occurred.connect(self.on_task_error)
        # finished нужен только для очистки
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.active_threads.discard(thread))
        thread.finished.connect(thread.deleteLater)

        thread.start()

    def stop_current_command(self):
        """Запускает остановку текущего процесса."""
        if self.running_command_name is None:
            # Эта проверка тоже не должна срабатывать при правильном UI state
             QMessageBox.information(self, "Информация", "Нет активной команды для остановки.")
             return

        self._set_ui_state_busy("stop") # Блокируем UI на время старта потока

        thread = QThread()
        worker = CommandWorker(process_name="winws.exe")
        worker.moveToThread(thread)
        self.active_threads.add(thread)
        thread.worker = worker

        thread.started.connect(worker.stop_command)
        worker.process_stopped.connect(self.on_process_stopped)
        worker.error_occurred.connect(self.on_task_error)
        # finished нужен только для очистки
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.active_threads.discard(thread))
        thread.finished.connect(thread.deleteLater)

        thread.start()

    # --- Слоты для обработки сигналов от Worker ---

    def on_command_started(self, started_command_name):
        """Слот: команда успешно передана для запуска."""
        # Переключаем UI в состояние "можно остановить"
        self._set_ui_state_can_stop(started_command_name)

    def on_process_stopped(self, success_message):
        """Слот: процесс успешно остановлен (или не найден)."""
        QMessageBox.information(self, "Остановка завершена", success_message)
        # Переключаем UI в состояние "можно запускать"
        self._set_ui_state_can_start()

    def on_task_error(self, error_message, command_name):
        """Слот: произошла ошибка при запуске или остановке."""
        QMessageBox.warning(self, "Ошибка", error_message)
        # Возвращаем UI в предыдущее рабочее состояние
        if command_name is not None: # Ошибка при запуске
            self._set_ui_state_can_start()
        else: # Ошибка при остановке
            # Восстанавливаем состояние "можно остановить", т.к. команда могла не остановиться
            if self.running_command_name:
                 self._set_ui_state_can_stop(self.running_command_name)
            else:
                 # Если running_command_name почему-то None, просто возвращаем в старт
                 self._set_ui_state_can_start()

    # --- Обработка закрытия окна ---
    def closeEvent(self, event: QCloseEvent):
        """Переопределенный метод, вызывается при закрытии окна."""
        reply = QMessageBox.question(self, 'Подтверждение',
                                     "Завершить работу и остановить процесс 'winws.exe'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.running_command_name:
                 button = self.command_buttons.get(self.running_command_name)
                 if button:
                     button.setStyleSheet(self.DEFAULT_STYLE)
            try:
                commands.stop_process("winws.exe")
            except Exception as e:
                 QMessageBox.critical(self, "Ошибка при закрытии",
                                      f"Не удалось остановить winws.exe:\n{e}")
            self.running_command_name = None
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CommandRunnerApp()
    window.show()
    sys.exit(app.exec())
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QScrollArea,
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QCloseEvent

# Импорт вашего модуля команд
from src.scripts import commands


class CommandWorker(QObject):
    command_started = pyqtSignal(str)
    process_stopped = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)  # message, command_name (None if stop error)
    finished = pyqtSignal()

    def __init__(self, command_name=None, process_name=None):
        super().__init__()
        self._command_name = command_name
        self._process_name = process_name

    def run_command(self):
        if not self._command_name:
            self.error_occurred.emit(
                "Worker: Не указано имя команды.", self._command_name
            )
            self.finished.emit()
            return
        try:
            commands.run_zapret_command(self._command_name)
            self.command_started.emit(self._command_name)
        except Exception as e:
            self.error_occurred.emit(
                f"Ошибка при запуске '{self._command_name}':\n{e}", self._command_name
            )
        finally:
            self.finished.emit()

    def stop_command(self):
        """Функция для остановки процесса по имени."""
        if not self._process_name:
            self.error_occurred.emit("Worker: Не указано имя процесса.", None)
        else:
            success_flag = commands.stop_process(self._process_name)
            if success_flag:
                self.process_stopped.emit(
                    f"Процесс '{self._process_name}' завершил работу."
                )
            else:
                self.error_occurred.emit(
                    f"Не удалось остановить '{self._process_name}'.", None
                )
        self.finished.emit()


# --- Основной класс приложения ---
class CommandRunnerApp(QWidget):
    RUNNING_STYLE = "background-color: lightgreen; color: black;"
    DEFAULT_STYLE = ""  # Пустая строка сбрасывает стиль к значению по умолчанию

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                color: white;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QScrollArea {
                border: 1px solid #3a3a3a;
            }
        """)
        self.setWindowTitle("Zapret")
        self.setGeometry(200, 200, 500, 350)
        self.setFixedSize(self.size())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
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
            button.clicked.connect(
                lambda checked, name=command_name: self.run_selected_command(name)
            )
            cmd_layout.addWidget(button)
            self.command_buttons[command_name] = button

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cmd_buttons_widget)
        self.main_layout.addWidget(scroll)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.ico"))

        tray_menu = QMenu()

        restore_action = QAction("Восстановить", self)
        restore_action.triggered.connect(self.show_normal)
        tray_menu.addAction(restore_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.tray_icon_clicked)

        self._set_ui_state_can_start()

    def show_normal(self) -> None:
        """Восстановление окна из трея"""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()

    def tray_icon_clicked(self, reason) -> None:
        """Обработка кликов по иконке в трее"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal()

    def _set_ui_state_can_start(self):
        if self.running_command_name:
            button = self.command_buttons.get(self.running_command_name)
            if button:
                button.setStyleSheet(self.DEFAULT_STYLE)

        self.running_command_name = None
        for button in self.command_buttons.values():
            button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _set_ui_state_can_stop(self, command_name):
        if self.running_command_name and self.running_command_name != command_name:
            old_button = self.command_buttons.get(self.running_command_name)
            if old_button:
                old_button.setStyleSheet(self.DEFAULT_STYLE)

        self.running_command_name = command_name
        for btn_name, button in self.command_buttons.items():
            if btn_name == command_name:
                button.setEnabled(True)
                button.setStyleSheet(self.RUNNING_STYLE)
            else:
                button.setEnabled(False)
                button.setStyleSheet(self.DEFAULT_STYLE)
        self.stop_button.setEnabled(True)
        self.stop_button.setStyleSheet("background-color: #800000;")

    def _set_ui_state_busy(self, operation_type="start"):
        for button in self.command_buttons.values():
            button.setEnabled(False)
        self.stop_button.setEnabled(False)

    # --- Методы запуска/остановки ---

    def run_selected_command(self, command_name):
        if self.running_command_name is not None:
            QMessageBox.warning(
                self,
                "Запрещено",
                f"Команда '{self.running_command_name}' уже выполняется.",
            )
            return

        self._set_ui_state_busy("start")
        thread = QThread()
        worker = CommandWorker(command_name=command_name)
        worker.moveToThread(thread)
        self.active_threads.add(thread)
        thread.worker = worker

        thread.started.connect(worker.run_command)
        worker.command_started.connect(self.on_command_started)
        worker.error_occurred.connect(self.on_task_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.active_threads.discard(thread))
        thread.finished.connect(thread.deleteLater)

        thread.start()

    def stop_current_command(self):
        if self.running_command_name is None:
            QMessageBox.information(
                self, "Информация", "Нет активной команды для остановки."
            )
            return

        self._set_ui_state_busy("stop")
        thread = QThread()
        worker = CommandWorker(process_name="winws.exe")
        worker.moveToThread(thread)
        self.active_threads.add(thread)
        thread.worker = worker

        thread.started.connect(worker.stop_command)
        worker.process_stopped.connect(self.on_process_stopped)
        worker.error_occurred.connect(self.on_task_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.active_threads.discard(thread))
        thread.finished.connect(thread.deleteLater)

        thread.start()

    # --- Слоты для обработки сигналов от Worker ---

    def on_command_started(self, started_command_name):
        self._set_ui_state_can_stop(started_command_name)

    def on_process_stopped(self, success_message):
        QMessageBox.information(self, "Остановка завершена", success_message)
        self._set_ui_state_can_start()

    def on_task_error(self, error_message, command_name):
        QMessageBox.warning(self, "Ошибка", error_message)
        if command_name is not None:
            self._set_ui_state_can_start()
        else:
            if self.running_command_name:
                self._set_ui_state_can_stop(self.running_command_name)
            else:
                self._set_ui_state_can_start()

    def closeEvent(self, event: QCloseEvent):
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Завершить работу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.running_command_name:
                button = self.command_buttons.get(self.running_command_name)
                if button:
                    button.setStyleSheet(self.DEFAULT_STYLE)
            try:
                commands.stop_process("winws.exe")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка при закрытии",
                    f"Не удалось остановить winws.exe:\n{e}",
                )
            self.running_command_name = None
            event.accept()
        else:
            event.ignore()

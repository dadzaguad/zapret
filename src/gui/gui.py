import os

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QScrollArea,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer, Qt, QEvent
from PyQt6.QtGui import QCloseEvent, QAction, QIcon

from src.gui.resource_utils import resource_path
from src.scripts.commands import ZapretRunner


class CommandWorker(QObject):
    command_started = pyqtSignal(str)
    process_stopped = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, zapret_runner: ZapretRunner, command_name=None):
        super().__init__()
        self._zapret_runner = zapret_runner
        self._command_name = command_name

    def run_command(self) -> None:
        if not self._command_name:
            self.error_occurred.emit(
                "Worker: Не указано имя команды.", self._command_name
            )
            self.finished.emit()
            return
        try:
            self._zapret_runner.run(self._command_name)
            self.command_started.emit(self._command_name)
        except Exception as e:
            self.error_occurred.emit(
                f"Ошибка при запуске '{self._command_name}':\n{e}", self._command_name
            )
        finally:
            self.finished.emit()

    def stop_command(self) -> None:
        try:
            self._zapret_runner.terminate()
            self.process_stopped.emit("Процесс завершен.")
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при остановке процесса:\n{e}", None)
        finally:
            self.finished.emit()


class CommandRunnerApp(QWidget):
    RUNNING_STYLE = "background-color: lightgreen; color: black;"
    DEFAULT_STYLE = "font-size: 14px;"

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            """
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
        """
        )
        self.setWindowTitle("Zapret")
        self.setGeometry(200, 200, 500, 350)
        self.setFixedSize(self.size())
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint
        )
        self.main_layout = QVBoxLayout(self)
        self.active_threads = set()
        self.command_buttons = {}
        self.running_command_name = None
        self.pending_command = None
        self.zapret_runner = ZapretRunner()

        cmd_buttons_widget = QWidget()
        cmd_layout = QVBoxLayout()
        cmd_buttons_widget.setLayout(cmd_layout)
        cmd_buttons_widget.setLayout(cmd_layout)
        cmd_layout.addWidget(QLabel("Запуск профиля:"))

        for command_name in self.zapret_runner.commands.keys():
            button = QPushButton(command_name)
            button.setStyleSheet(self.DEFAULT_STYLE)
            button.setMinimumHeight(30)
            button.clicked.connect(
                lambda checked, name=command_name: self.handle_command_button(name)
            )
            cmd_layout.addWidget(button)
            self.command_buttons[command_name] = button

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cmd_buttons_widget)
        self.main_layout.addWidget(scroll)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.ico"))
        icon_path = resource_path("icon.ico")
        if not os.path.exists(icon_path):
            # Альтернативный путь для PyInstaller
            icon_path = resource_path(os.path.join("src", "gui", "icon.ico"))

        self.tray_icon.setIcon(QIcon(icon_path))
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
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized
            | Qt.WindowState.WindowActive
        )
        self.activateWindow()

    def tray_icon_clicked(self, reason) -> None:
        """Обработка кликов по иконке в трее"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal()

    def changeEvent(self, event) -> None:
        """Обработка изменения состояния окна (сворачивание)"""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                if QSystemTrayIcon.isSystemTrayAvailable():
                    self.hide()
                else:
                    self.showMinimized()
        super().changeEvent(event)

    def handle_command_button(self, command_name: str) -> None:
        if self.running_command_name == command_name:
            self._stop_current_command()
        else:
            if self.running_command_name:
                self.pending_command = command_name
                self._stop_current_command()
            else:
                self._run_selected_command(command_name)

    def _set_ui_state_can_start(self) -> None:
        if self.running_command_name:
            button = self.command_buttons.get(self.running_command_name)
            if button:
                button.setStyleSheet(self.DEFAULT_STYLE)

        self.running_command_name = None

        if self.pending_command:
            command_to_run = self.pending_command
            self.pending_command = None
            QTimer.singleShot(100, lambda: self._run_selected_command(command_to_run))
        else:
            for button in self.command_buttons.values():
                button.setEnabled(True)

    def _set_ui_state_can_stop(self, command_name) -> None:
        if self.running_command_name:
            old_button = self.command_buttons.get(self.running_command_name)
            if old_button:
                old_button.setStyleSheet(self.DEFAULT_STYLE)

        self.running_command_name = command_name

        button = self.command_buttons.get(command_name)
        if button:
            button.setStyleSheet(self.RUNNING_STYLE)

        for btn in self.command_buttons.values():
            btn.setEnabled(True)

    def _set_ui_state_busy(self) -> None:
        for button in self.command_buttons.values():
            button.setEnabled(False)

    def _run_selected_command(self, command_name) -> None:
        self._set_ui_state_busy()
        thread = QThread()
        worker = CommandWorker(self.zapret_runner, command_name=command_name)
        worker.moveToThread(thread)
        self.active_threads.add(thread)
        thread.worker = worker

        thread.started.connect(worker.run_command)
        worker.command_started.connect(self._on_command_started)
        worker.error_occurred.connect(self._on_task_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.active_threads.discard(thread))
        thread.finished.connect(thread.deleteLater)

        thread.start()

    def _stop_current_command(self) -> None:
        if self.running_command_name is None:
            return

        self._set_ui_state_busy()
        thread = QThread()
        worker = CommandWorker(self.zapret_runner)
        worker.moveToThread(thread)
        self.active_threads.add(thread)
        thread.worker = worker

        thread.started.connect(worker.stop_command)
        worker.process_stopped.connect(self._on_process_stopped)
        worker.error_occurred.connect(self._on_task_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.active_threads.discard(thread))
        thread.finished.connect(thread.deleteLater)

        thread.start()

    def _on_command_started(self, started_command_name) -> None:
        self._set_ui_state_can_stop(started_command_name)

    def _on_process_stopped(self, success_message) -> None:
        self._set_ui_state_can_start()

    def _on_task_error(self, error_message, command_name) -> None:
        QMessageBox.warning(self, "Ошибка", error_message)
        if command_name is not None:
            self._set_ui_state_can_start()
        else:
            if self.running_command_name:
                self._set_ui_state_can_stop(self.running_command_name)
            else:
                self._set_ui_state_can_start()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.running_command_name:
            msg = QMessageBox(self)
            msg.setWindowTitle("Подтверждение")
            msg.setText(
                "Вы уверены, что хотите выйти? Некоторые процессы могут быть остановлены."
            )
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg.setDefaultButton(QMessageBox.StandardButton.No)

            yes_btn = msg.button(QMessageBox.StandardButton.Yes)
            no_btn = msg.button(QMessageBox.StandardButton.No)
            yes_btn.setMinimumWidth(50)
            no_btn.setMinimumWidth(50)

            yes_btn.setMinimumHeight(20)
            no_btn.setMinimumHeight(20)

            result = msg.exec()
            if result == QMessageBox.StandardButton.No:
                event.ignore()
                return

        if self.running_command_name:
            try:
                self.zapret_runner.terminate()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Ошибка при остановке процесса: {str(e)}",
                )

        for thread in list(self.active_threads):
            thread.quit()
            thread.wait()

        self.tray_icon.hide()

        event.accept()

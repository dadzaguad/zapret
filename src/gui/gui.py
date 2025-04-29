import os
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QLabel,
    QScrollArea,
    QSystemTrayIcon,
    QMenu,
    QApplication,
)
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer, Qt, QEvent
from PyQt6.QtGui import QCloseEvent, QAction, QIcon

from src.gui.resource_utils import resource_path
from src.scripts.commands import ZapretRunner
from src.gui.translations import translator


class CommandWorker(QObject):
    command_started: pyqtSignal = pyqtSignal(str)
    process_stopped: pyqtSignal = pyqtSignal(str)
    error_occurred: pyqtSignal = pyqtSignal(str, str)
    finished: pyqtSignal = pyqtSignal()

    def __init__(self, zapret_runner: ZapretRunner, command_name: Optional[str] = None):
        super().__init__()
        self._zapret_runner: ZapretRunner = zapret_runner
        self._command_name: Optional[str] = command_name

    def run_command(self) -> None:
        if self._command_name is None:
            self.finished.emit()
            return
        try:
            self._zapret_runner.run(self._command_name)
            self.command_started.emit(self._command_name)
        except Exception as e:
            self.error_occurred.emit(str(e), self._command_name)
        finally:
            self.finished.emit()

    def stop_command(self) -> None:
        try:
            self._zapret_runner.terminate()
            self.process_stopped.emit(
                translator.translate("process_completed", "Process completed")
            )
        except RuntimeError as e:
            self.error_occurred.emit(str(e), None)
        finally:
            self.finished.emit()


class CommandRunnerApp(QWidget):
    RUNNING_STYLE: str = "background-color: lightgreen; color: black;"
    DEFAULT_STYLE: str = ""

    def __init__(self, zapret_runner: ZapretRunner):
        super().__init__()

        icon_path: str = resource_path("icon.ico")
        if not os.path.exists(icon_path):
            icon_path = resource_path(os.path.join("src", "gui", "icon.ico"))

        app_icon: QIcon = QIcon(icon_path)
        self.setWindowIcon(app_icon)

        self.tray_icon: QSystemTrayIcon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(app_icon)

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

        self.main_layout: QVBoxLayout = QVBoxLayout(self)
        self._active_threads: set[QThread] = set()
        self._command_buttons: dict[str, QPushButton] = {}
        self._running_command_name: Optional[str] = None
        self._pending_command: Optional[str] = None
        self.zapret_runner: ZapretRunner = zapret_runner

        cmd_buttons_widget: QWidget = QWidget()
        cmd_layout: QVBoxLayout = QVBoxLayout()
        cmd_buttons_widget.setLayout(cmd_layout)
        cmd_layout.addWidget(
            QLabel(translator.translate("profile_start", "Profile start"))
        )

        if hasattr(self.zapret_runner, "commands") and self.zapret_runner.commands:
            for command_name in self.zapret_runner.commands.keys():
                button: QPushButton = QPushButton(command_name)
                button.setStyleSheet(self.DEFAULT_STYLE)
                button.setMinimumHeight(30)
                button.clicked.connect(
                    lambda checked, name=command_name: self.handle_command_button(name)
                )
                cmd_layout.addWidget(button)
                self._command_buttons[command_name] = button
        else:
            no_commands_label = QLabel(
                translator.translate("no_commands_loaded", "No commands found.")
            )
            cmd_layout.addWidget(no_commands_label)

        scroll: QScrollArea = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cmd_buttons_widget)
        self.main_layout.addWidget(scroll)

        tray_menu: QMenu = QMenu()
        restore_action: QAction = QAction(
            translator.translate("restore", "Restore"), self
        )
        restore_action.triggered.connect(self.show_normal)
        tray_menu.addAction(restore_action)

        exit_action: QAction = QAction(translator.translate("exit", "Exit"), self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_clicked)

        self._set_ui_state_can_start()

    def show_normal(self) -> None:
        self.show()
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized
            | Qt.WindowState.WindowActive
        )
        self.activateWindow()

    def tray_icon_clicked(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal()

    def changeEvent(self, event: Optional[QEvent]) -> None:
        super().changeEvent(event)

    def handle_command_button(self, command_name: str) -> None:
        if self._running_command_name == command_name:
            self._stop_current_command()
        else:
            if self._running_command_name:
                self._pending_command = command_name
                self._stop_current_command()
            else:
                self._run_selected_command(command_name)

    def _set_ui_state_can_start(self) -> None:
        if self._running_command_name:
            button: Optional[QPushButton] = self._command_buttons.get(
                self._running_command_name
            )
            if button:
                button.setStyleSheet(self.DEFAULT_STYLE)
        self._running_command_name = None
        if self._pending_command:
            command_to_run: str = self._pending_command
            self._pending_command = None
            QTimer.singleShot(100, lambda: self._run_selected_command(command_to_run))
        else:
            for button in self._command_buttons.values():
                button.setEnabled(True)

    def _set_ui_state_can_stop(self, command_name: str) -> None:
        if self._running_command_name and self._running_command_name != command_name:
            old_button: Optional[QPushButton] = self._command_buttons.get(
                self._running_command_name
            )
            if old_button:
                old_button.setStyleSheet(self.DEFAULT_STYLE)
        self._running_command_name = command_name
        button: Optional[QPushButton] = self._command_buttons.get(command_name)
        if button:
            button.setStyleSheet(self.RUNNING_STYLE)
        for btn in self._command_buttons.values():
            btn.setEnabled(True)

    def _set_ui_state_busy(self) -> None:
        for button in self._command_buttons.values():
            button.setEnabled(False)

    def _run_selected_command(self, command_name: str) -> None:
        self._set_ui_state_busy()
        thread: QThread = QThread()
        worker: CommandWorker = CommandWorker(
            self.zapret_runner, command_name=command_name
        )
        worker.moveToThread(thread)
        self._active_threads.add(thread)
        thread.worker = worker
        thread.started.connect(worker.run_command)
        worker.command_started.connect(self._on_command_started)
        worker.error_occurred.connect(self._on_task_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda t=thread: self._active_threads.discard(t))
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _stop_current_command(self) -> None:
        if self._running_command_name is None:
            self._set_ui_state_can_start()
            return
        self._set_ui_state_busy()
        thread: QThread = QThread()
        worker: CommandWorker = CommandWorker(self.zapret_runner)
        worker.moveToThread(thread)
        self._active_threads.add(thread)
        thread.worker = worker
        thread.started.connect(worker.stop_command)
        worker.process_stopped.connect(self._on_process_stopped)
        worker.error_occurred.connect(self._on_task_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda t=thread: self._active_threads.discard(t))
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _on_command_started(self, started_command_name: str) -> None:
        self._set_ui_state_can_stop(started_command_name)

    def _on_process_stopped(self, success_message: str) -> None:
        self._set_ui_state_can_start()

    def _on_task_error(self, error_message: str, command_name: Optional[str]) -> None:
        QMessageBox.warning(self, translator.translate("error", "Error"), error_message)
        if command_name is not None:
            self._set_ui_state_can_start()
        else:
            if self._running_command_name:
                self._set_ui_state_can_stop(self._running_command_name)
            else:
                self._set_ui_state_can_start()

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:
        """Обрабатывает нажатие на крестик окна."""
        if not event:
            return

        if self._running_command_name:
            self.hide()

            event.ignore()

    def cleanup_and_accept_close(self, event: Optional[QCloseEvent]):
        """Выполняет очистку и принимает событие закрытия."""
        for thread in list(self._active_threads):
            if thread.isRunning():
                thread.quit()
                if not thread.wait(500):
                    print(f"Warning: Thread {thread} did not finish gracefully.")

        self.tray_icon.hide()
        if event:
            event.accept()

    def quit_application(self) -> None:
        """Принудительно завершает приложение (вызывается из трей-меню)."""
        if self._running_command_name:
            try:
                self.zapret_runner.terminate()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    translator.translate("error", "Ошибка"),
                    f"{translator.translate('process_stop_error', 'Ошибка при остановке процесса при выходе')}: {str(e)}",
                )

        for thread in list(self._active_threads):
            if thread.isRunning():
                thread.quit()
                if not thread.wait(500):
                    print(
                        f"Warning: Thread {thread} did not finish gracefully on forced quit."
                    )

        self.tray_icon.hide()
        QApplication.instance().quit()

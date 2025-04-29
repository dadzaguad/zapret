import sys
import ctypes
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.core.admin_utils import is_admin, restart_as_admin, show_critical_error
from src.gui.gui import CommandRunnerApp
from src.scripts.commands import ZapretRunner
from src.gui.translations import translator

APP_GUID = "{2470b8b0-e497-41e4-a51d-d2dd745535ac}"
_instance_mutex_handle = None
is_first_instance = False

if __name__ == "__main__":

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    ERROR_ALREADY_EXISTS = 183
    SW_RESTORE = 9

    try:
        mutex_name = f"Global\\{APP_GUID}_ZapretAppMutex"
        _instance_mutex_handle = kernel32.CreateMutexW(None, True, mutex_name)
        last_error = kernel32.GetLastError()

        if last_error == ERROR_ALREADY_EXISTS:
            try:
                window_title = "Zapret"
                hwnd = user32.FindWindowW(None, window_title)
                if hwnd:
                    user32.ShowWindow(hwnd, SW_RESTORE)
                    user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
            finally:
                if _instance_mutex_handle:
                    kernel32.CloseHandle(_instance_mutex_handle)
                sys.exit(0)

        elif last_error == 0 and _instance_mutex_handle:
            is_first_instance = True

        else:
            raise ctypes.WinError(last_error)

    except Exception as e:
        error_msg = f"{translator.translate('mutex_error_message', 'Failed to check if the application is already running:')}\n{e}"
        show_critical_error("mutex_error_title", "Startup Error", error_msg, translator)
        if _instance_mutex_handle:
            kernel32.CloseHandle(_instance_mutex_handle)
        sys.exit(1)

    exit_code = 1
    try:
        if not is_admin():
            restart_as_admin(translator)
            sys.exit(1)

        app = QApplication(sys.argv)
        try:
            zapret_runner_instance = ZapretRunner()
            window = CommandRunnerApp(zapret_runner=zapret_runner_instance)
            window.show()
            exit_code = app.exec()

        except RuntimeError as e:
            QMessageBox.critical(
                None,
                translator.translate(
                    "initialization_error_title", "Initialization Error"
                ),
                f"{translator.translate('initialization_error_message', 'Failed to initialize/run the application:')}\n{e}",
            )
            exit_code = 1
        except Exception as e:
            QMessageBox.critical(
                None,
                translator.translate("critical_error_title", "Critical Error"),
                f"{translator.translate('unexpected_error_message', 'An unexpected error occurred:')}\n{e}",
            )
            exit_code = 1

    except Exception as e:
        error_msg = f"{translator.translate('startup_error_message', 'A critical error occurred during startup:')}\n{e}"
        show_critical_error(
            "startup_error_title", "Startup Error", error_msg, translator
        )
        exit_code = 1
    finally:
        if is_first_instance and _instance_mutex_handle:
            kernel32.ReleaseMutex(_instance_mutex_handle)
            kernel32.CloseHandle(_instance_mutex_handle)
        sys.exit(exit_code)

import os
import json
import shlex
import subprocess
from typing import Final

from src.gui.translations import translator


SCRIPT_DIR: Final[str] = os.path.dirname(os.path.abspath(__file__))


class ZapretRunner:
    _instance = None
    commands: dict[str, str] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            instance = super().__new__(cls, *args, **kwargs)
            cls._instance = instance
        return cls._instance

    def __init__(self):
        self._current_process: subprocess.Popen | None = None
        self._load_commands()

    @classmethod
    def _load_commands(cls) -> None:
        commands_path = os.path.join(SCRIPT_DIR, "commands.json")
        try:
            with open(commands_path, "r", encoding="utf-8") as f:
                commands_data = json.load(f)
                cls.commands = {
                    name: data["args"] for name, data in commands_data.items()
                }
        except Exception as e:
            raise RuntimeError(f"Failed to load commands: {str(e)}")

    def run(self, command_name: str) -> None:
        if command_name not in self.commands:
            raise ValueError(f"Command '{command_name}' not found")

        winws_exe_path = os.path.join(SCRIPT_DIR, "bin", "winws.exe")
        winws_args = self.commands[command_name]
        args = [winws_exe_path] + shlex.split(winws_args)

        self._current_process = subprocess.Popen(
            args,
            cwd=SCRIPT_DIR,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                | subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS
            ),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            shell=False,
        )
        return_code = self._current_process.poll()
        if return_code is not None and return_code != 0:
            self._current_process.stderr.close()
            raise RuntimeError(
                translator.translate(
                    "process_immediate_exit",
                    f"Error while starting Zapret process. Error code: {return_code}",
                )
            )

    def terminate(self) -> None:
        if self._current_process is None:
            raise RuntimeError(
                translator.translate("process_not_launched", "Process is not launched")
            )
        try:
            self._current_process.terminate()
            self._current_process = None
        except Exception:
            raise RuntimeError(
                translator.translate(
                    "process_stop_error", "Error while stopping process"
                )
            )

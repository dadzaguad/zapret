import json
import shlex
import subprocess
import os
from src.gui.translations import translator


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_PATH = os.path.join(SCRIPT_DIR, "bin")


class ZapretRunner:
    def __init__(self):
        self._current_process = None
        self.commands = self._load_commands()

    def _get_commands(self) -> dict[str, str]:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        commands_path = os.path.join(script_dir, "commands.json")

        try:
            with open(commands_path, "r", encoding="utf-8") as f:
                commands_data = json.load(f)
                return {name: data["args"] for name, data in commands_data.items()}
        except Exception as e:
            raise RuntimeError(f"Failed to load commands: {str(e)}")

    def run(self, command_name: str) -> None:
        if command_name not in self.commands:
            raise ValueError(f"Command '{command_name}' not found")

        winws_exe_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "bin", "winws.exe"
        )
        winws_args = self.commands[command_name]

        args = [winws_exe_path] + shlex.split(winws_args)

        self._current_process = subprocess.Popen(
            args,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                | subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS
            ),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            shell=False,
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

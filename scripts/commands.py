import subprocess
import os
import sys
import ctypes

# --- Конфигурация путей ---
# Определяем директорию, где находится ЭТОТ файл
# Предполагается, что check_updates.bat, папка bin/, list-general.txt и т.д.
# находятся в той же директории или имеют ту же относительную структуру.
try:
    # __file__ содержит путь к текущему модулю
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Обработка случая, если __file__ не определен (например, в интерактивной сессии)
    SCRIPT_DIR = os.getcwd() # Используем текущую рабочую директорию как запасной вариант
# Путь к папке bin относительно директории скрипта
BIN_PATH = os.path.join(SCRIPT_DIR, 'bin')

# --- Хранилище аргументов для команд ---
# Словарь: ключ - имя команды, значение - строка с аргументами для winws.exe
# Пути к файлам .bin формируются динамически с использованием BIN_PATH
COMMAND_ARGS = {
    "general": f"""
        --wf-tcp=80,443 --wf-udp=443,50000-50100
        --filter-udp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --new
        --filter-tcp=80 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new
        --filter-tcp=443 --hostlist="list-general.txt" --dpi-desync=fake,split --dpi-desync-autottl=2 --dpi-desync-repeats=6 --dpi-desync-fooling=badseq --dpi-desync-fake-tls="{os.path.join(BIN_PATH, 'tls_clienthello_www_google_com.bin')}"
    """,
    "general-alt": f"""
        --wf-tcp=80,443 --wf-udp=443,50000-50100
        --filter-udp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --new
        --filter-tcp=80 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new
        --filter-tcp=443 --hostlist="list-general.txt" --dpi-desync=fake,split --dpi-desync-autottl=5 --dpi-desync-repeats=6 --dpi-desync-fooling=badseq --dpi-desync-fake-tls="{os.path.join(BIN_PATH, 'tls_clienthello_www_google_com.bin')}"
    """,
    "general-mgts": f"""
        --wf-tcp=80,443 --wf-udp=443,50000-50100
        --filter-udp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --new
        --filter-tcp=80 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new
        --filter-tcp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fooling=md5sig --dpi-desync-fake-tls="{os.path.join(BIN_PATH, 'tls_clienthello_www_google_com.bin')}"
    """,
    "general-mgts-2": f"""
        --wf-tcp=80,443 --wf-udp=443,50000-50100
        --filter-udp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --new
        --filter-tcp=80 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new
        --filter-tcp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fooling=md5sig --dpi-desync-fake-tls="{os.path.join(BIN_PATH, 'tls_clienthello_www_google_com.bin')}"
    """,
    "general-alt-4": f"""
        --wf-tcp=80,443 --wf-udp=443,50000-50100
        --filter-udp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=8 --new
        --filter-tcp=80 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new
        --filter-tcp=443 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-repeats=6 --dpi-desync-fooling=md5sig --dpi-desync-fake-tls="{os.path.join(BIN_PATH, 'tls_clienthello_www_google_com.bin')}"
    """,
    "general-alt-3": f"""
        --wf-tcp=80,443 --wf-udp=443,50000-50100 
        --filter-udp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --new
        --filter-tcp=80 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new
        --filter-tcp=443 --hostlist="list-general.txt" --dpi-desync=split --dpi-desync-split-pos=1 --dpi-desync-autottl --dpi-desync-fooling=badseq --dpi-desync-repeats=8
    """,
    "general-alt-2": f"""
        --wf-tcp=80,443 --wf-udp=443,50000-50100
        --filter-udp=443 --hostlist="list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --new
        --filter-tcp=80 --hostlist="list-general.txt" --dpi-desync=fake,split2 --dpi-desync-autottl=2 --dpi-desync-fooling=md5sig --new
        --filter-tcp=443 --hostlist="list-general.txt" --dpi-desync=split2 --dpi-desync-split-seqovl=652 --dpi-desync-split-pos=2 --dpi-desync-split-seqovl-pattern="{os.path.join(BIN_PATH, 'tls_clienthello_www_google_com.bin')}"
    """,
    "discord": f"""
        --wf-tcp=443 --wf-udp=443,50000-50100
        --filter-udp=443 --hostlist="list-discord.txt" --dpi-desync=fake --dpi-desync-repeats=6 --dpi-desync-fake-quic="{os.path.join(BIN_PATH, 'quic_initial_www_google_com.bin')}" --new
        --filter-udp=50000-50100 --ipset="ipset-discord.txt" --dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-cutoff=d3 --dpi-desync-repeats=6 --new
        --filter-tcp=443 --hostlist="list-discord.txt" --dpi-desync=fake,split --dpi-desync-autottl=2 --dpi-desync-repeats=6 --dpi-desync-fooling=badseq --dpi-desync-fake-tls="{os.path.join(BIN_PATH, 'tls_clienthello_www_google_com.bin')}"
    """
}

# --- Вспомогательная функция для запуска check_updates.bat ---
def _run_check_updates():
    """(Внутренняя) Запускает check_updates.bat soft."""
    print("Запуск check_updates.bat...")
    try:
        # Используем cmd /c call для корректного вызова .bat
        process = subprocess.run(
            ['cmd', '/c', 'call', 'check_updates.bat', 'soft'],
            cwd=SCRIPT_DIR, # Рабочая директория - папка с zapret_runner.py
            check=True,     # Вызвать исключение при ошибке в .bat
            capture_output=True, # Подавить вывод .bat (кроме ошибок)
            text=True,      # Работать с текстом
            encoding='utf-8', # Использовать UTF-8 (как chcp 65001)
            errors='ignore' # Игнорировать ошибки декодирования
        )
        # print("STDOUT check_updates:", process.stdout) # Раскомментируйте для отладки
        print("check_updates.bat выполнен успешно.")
        return True
    except FileNotFoundError:
        print(f"Ошибка: Файл 'check_updates.bat' не найден в директории {SCRIPT_DIR}", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении 'check_updates.bat': Код возврата {e.returncode}", file=sys.stderr)
        # Выводим stderr от .bat, если он есть и содержит информацию
        if e.stderr:
            print(f"--- STDERR check_updates.bat ---\n{e.stderr}\n-----------------------------", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при запуске check_updates.bat: {e}", file=sys.stderr)
        return False

# --- Основная функция для запуска команд ---
def run_zapret_command(command_name: str):
    """
    Запускает выбранную команду zapret с помощью 'start' в фоновом режиме,
    не дожидаясь завершения winws.exe.
    """

    print(f"\nПопытка запуска профиля: '{command_name}'")

    winws_args = COMMAND_ARGS[command_name]
    winws_exe_path = os.path.join(BIN_PATH, 'winws.exe')

    full_command = f'start "zapret: {command_name}" /min "{winws_exe_path}" {winws_args}'
    command_cleaned = " ".join(full_command.split())


    # Используем Popen для неблокирующего запуска в фоне
    subprocess.Popen(
        command_cleaned,
        shell=True,         # Нужно для команды 'start'
        cwd=SCRIPT_DIR,     # Устанавливаем рабочую директорию
        # Следующие флаги помогают отсоединить процесс от родительского (Python скрипта)
        # Особенно актуально для Windows при использовании shell=True
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        stdout=subprocess.DEVNULL, # Перенаправляем вывод, чтобы не ждать его
        stderr=subprocess.DEVNULL  # Перенаправляем ошибки, чтобы не ждать их
    )
    # Popen возвращает управление немедленно после запуска команды 'start'
    print(f"Команда '{command_name}' передана системе для запуска.")


def stop_process(process_name):
    """Останавливает процесс по имени исполняемого файла с помощью taskkill."""
    print(f"Попытка остановить процесс: {process_name}")

    try:
        # Команда для принудительного завершения процесса по имени
        # /F - принудительное завершение
        # /IM - указание имени образа (исполняемого файла)
        # /T - завершить процесс и все его дочерние процессы (на всякий случай)
        cmd = f'taskkill /F /IM "{process_name}" /T'
        print(f"Выполнение команды: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp866', errors='ignore', check=False)

        # Проверяем вывод команды taskkill
        output = result.stdout + result.stderr
        # print(f"DEBUG: Taskkill output:\n{output}") # Для отладки

        if result.returncode == 0 or "успех" in output.lower() or "success" in output.lower():
            print(f"Команда taskkill успешно выполнена для {process_name}.")
            return True
        elif "не найден" in output.lower() or "not found" in output.lower():
             print(f"Процесс {process_name} не был найден командой taskkill (возможно, уже остановлен).")
             return True # Считаем успехом, если его и так нет
        else:
            print(f"Ошибка при выполнении taskkill для {process_name}.")
            print(f"Код возврата: {result.returncode}")
            print(f"Вывод taskkill:\n{output}")
            return False

    except FileNotFoundError:
        print(f"Ошибка: Команда 'taskkill' не найдена. Убедитесь, что она доступна в PATH.")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка при остановке {process_name}: {e}")
        return False
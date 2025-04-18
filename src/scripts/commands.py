import subprocess
import os


# --- Конфигурация путей ---
# Определяем директорию, где находится ЭТОТ файл
# Предполагается, что check_updates.bat, папка bin/, list-general.txt и т.д.
# находятся в той же директории или имеют ту же относительную структуру.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_PATH = os.path.join(SCRIPT_DIR, "bin")

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
    """,
}


# --- Основная функция для запуска команд ---
def run_zapret_command(command_name: str):
    """
    Запускает выбранную команду zapret с помощью 'start' в фоновом режиме,
    не дожидаясь завершения winws.exe.
    """

    winws_args = COMMAND_ARGS[command_name]
    winws_exe_path = os.path.join(BIN_PATH, "winws.exe")

    full_command = (
        f'start "zapret: {command_name}" /min "{winws_exe_path}" {winws_args}'
    )
    command_cleaned = " ".join(full_command.split())

    # Используем Popen для неблокирующего запуска в фоне
    subprocess.Popen(
        command_cleaned,
        shell=True,  # Нужно для команды 'start'
        cwd=SCRIPT_DIR,  # Устанавливаем рабочую директорию
        # Следующие флаги помогают отсоединить процесс от родительского (Python скрипта)
        # Особенно актуально для Windows при использовании shell=True
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        stdout=subprocess.DEVNULL,  # Перенаправляем вывод, чтобы не ждать его
        stderr=subprocess.DEVNULL,  # Перенаправляем ошибки, чтобы не ждать их
    )


def stop_process(process_name):
    """Останавливает процесс по имени исполняемого файла с помощью taskkill."""

    # Формируем и выполняем команду taskkill
    cmd = f'taskkill /F /IM "{process_name}" /T'
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="cp866",
        errors="ignore",
    )

    # Проверяем успешность выполнения команды
    if result.returncode == 0:
        return True
    return False

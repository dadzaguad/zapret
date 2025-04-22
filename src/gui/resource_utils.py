import os
import sys


def resource_path(relative_path):
    """Возвращает корректный путь для доступа к ресурсам после сборки в exe"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath("../..")

    return os.path.join(base_path, relative_path)
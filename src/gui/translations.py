import locale
import json
import os
import ctypes
from typing import Dict, Any


class Translator:
    def __init__(self):
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()
        self._current_lang = self._detect_system_language()

    def _load_translations(self) -> None:
        """Загружает переводы из JSON файлов"""
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            translations_path = os.path.join(base_path, "translations")

            for filename in os.listdir(translations_path):
                if filename.endswith(".json"):
                    lang = filename.split(".")[0]
                    with open(os.path.join(translations_path, filename), "r", encoding="utf-8") as f:
                        self._translations[lang] = json.load(f)
        except Exception as e:
            print(f"Error loading translations: {e}")
            self._translations = {}

    def _detect_system_language(self) -> str:
        """Определяет язык системы с помощью Windows API"""
        try:
            # Способ 1: Через Windows API
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            primary_lang = lang_id & 0x3FF
            if primary_lang == 0x19:  # Russian
                return "ru"

            # Способ 2: Через locale (резервный)
            sys_lang = locale.getdefaultlocale()[0]
            if sys_lang and "ru" in sys_lang.lower():
                return "ru"

            # Способ 3: Через переменные окружения (если предыдущие не сработали)
            if "LANG" in os.environ and "ru" in os.environ["LANG"].lower():
                return "ru"

        except Exception as e:
            print(f"Language detection error: {e}")

        return "en"  # По умолчанию английский

    def translate(self, key: str, default: str = "") -> str:
        """Возвращает перевод для указанного ключа"""
        if not self._translations:
            return default

        translation = self._translations.get(self._current_lang, {}).get(key)
        return translation if translation is not None else default


translator = Translator()
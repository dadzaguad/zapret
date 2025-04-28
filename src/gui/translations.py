import locale
import json
import os
import ctypes
from typing import Dict, Any
from src.gui.resource_utils import resource_path


class Translator:
    def __init__(self):
        self._translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()
        self._current_lang = self._detect_system_language()

    def _load_translations(self) -> None:
        """Загружает переводы из JSON файлов, используя resource_path"""
        try:
            translations_dir_path = resource_path("src/gui/translations")

            if not os.path.isdir(translations_dir_path):
                print(
                    f"Error: Translations directory not found at resolved path: {translations_dir_path}"
                )
                self._translations = {}
                return

            print(f"Loading translations from: {translations_dir_path}")

            for filename in os.listdir(translations_dir_path):
                if filename.endswith(".json"):
                    lang = filename.split(".")[0]
                    file_path = os.path.join(translations_dir_path, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            self._translations[lang] = json.load(f)
                        print(f"Loaded translation: {lang}")
                    except Exception as file_e:
                        print(f"Error loading translation file {filename}: {file_e}")

        except Exception as e:
            print(f"Error accessing translations directory: {e}")
            self._translations = {}

        if not self._translations:
            print("No translations were loaded.")
        else:
            print(f"Loaded languages: {list(self._translations.keys())}")

    def _detect_system_language(self) -> str:
        """Определяет язык системы с помощью Windows API"""
        detected_lang = "en"
        try:
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            primary_lang = lang_id & 0x3FF
            print(
                f"Detected system UI language ID: {lang_id} (Primary: {primary_lang})"
            )
            if primary_lang == 0x19:
                detected_lang = "ru"
            else:
                locale_lang = locale.getdefaultlocale()[0]
                print(f"Detected locale language: {locale_lang}")
                if locale_lang and "ru" in locale_lang.lower():
                    detected_lang = "ru"

        except Exception as e:
            print(f"Language detection error: {e}")

        print(f"Using language: {detected_lang}")
        return detected_lang

    def translate(self, key: str, default: str = "") -> str:
        """Возвращает перевод для указанного ключа"""
        lang_to_use = self._current_lang

        if not self._translations.get(lang_to_use):
            lang_to_use = "en"
            if not self._translations.get(lang_to_use):
                return default

        translation = self._translations.get(lang_to_use, {}).get(key)
        return translation if translation is not None else default


translator = Translator()

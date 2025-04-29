import locale
import json
import os
import ctypes
import sys
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


try:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        _BASE_PATH = sys._MEIPASS
    else:
        _BASE_PATH = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
except NameError:
    _BASE_PATH = os.path.abspath(".")


def resource_path(relative_path: str) -> str:
    """Возвращает абсолютный путь к ресурсу."""
    return os.path.join(_BASE_PATH, relative_path)


class Translator:
    def __init__(self):
        self._translations: Dict[str, Dict[str, str]] = {}
        self._current_lang: str = "en"
        self._load_translations()
        if self._translations:
            self._current_lang = self._detect_system_language()
        logging.info(f"Translator initialized. Using language: {self._current_lang}")

    def _load_translations(self) -> None:
        try:
            translations_dir = resource_path("src/gui/translations")
            if not os.path.isdir(translations_dir):
                logging.error(f"Translations directory not found: {translations_dir}")
                return

            logging.info(f"Loading translations from: {translations_dir}")
            loaded_langs = []
            for filename in os.listdir(translations_dir):
                if filename.endswith(".json"):
                    lang = filename.split(".")[0]
                    file_path = os.path.join(translations_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            self._translations[lang] = json.load(f)
                        loaded_langs.append(lang)
                    except json.JSONDecodeError as json_e:
                        logging.error(f"Error decoding JSON file {filename}: {json_e}")
                    except IOError as io_e:
                        logging.error(
                            f"Error reading translation file {filename}: {io_e}"
                        )
                    except Exception as e:
                        logging.error(
                            f"Unexpected error loading translation file {filename}: {e}"
                        )

            if loaded_langs:
                logging.info(f"Loaded languages: {', '.join(loaded_langs)}")
            else:
                logging.warning("No translations were successfully loaded.")

        except FileNotFoundError:
            logging.error(
                f"Base translations directory path incorrect or inaccessible."
            )
        except Exception as e:
            logging.error(f"Error accessing translations directory: {e}")

    def _detect_system_language(self) -> str:
        detected_lang = "en"

        try:
            if sys.platform == "win32":
                windll = ctypes.windll.kernel32
                lang_id = windll.GetUserDefaultUILanguage()
                primary_lang = lang_id & 0xFF
                # 0x09 = en, 0x19 = ru
                logging.info(
                    f"Detected WinAPI UI Language ID: {lang_id:#04x} (Primary: {primary_lang:#02x})"
                )
                if primary_lang == 0x19 and "ru" in self._translations:
                    detected_lang = "ru"
                    logging.info("Detected 'ru' via WinAPI UI Language.")
                    return detected_lang
        except Exception as e:
            logging.warning(f"Windows API language detection failed: {e}")

        try:
            locale_lang, _ = locale.getdefaultlocale()
            logging.info(f"Detected locale: {locale_lang}")
            if locale_lang:

                if locale_lang.lower().startswith("ru") and "ru" in self._translations:
                    detected_lang = "ru"
                    logging.info("Detected 'ru' via locale.")

        except Exception as e:
            logging.warning(f"Locale detection failed: {e}")

        if detected_lang == "ru" and "ru" not in self._translations:
            logging.warning(
                "Detected 'ru' but 'ru.json' not loaded. Falling back to 'en'."
            )
            return "en"
        elif "en" not in self._translations and detected_lang == "en":
            logging.warning(
                "'en.json' not loaded, but it's the default/fallback language."
            )

            return "en"

        return detected_lang

    def translate(self, key: str, default: Optional[str] = None) -> str:
        """Возвращает перевод для ключа или значение по умолчанию."""

        lang_dict = self._translations.get(self._current_lang)

        if lang_dict is None:
            lang_dict = self._translations.get("en")

        if lang_dict is None:
            return default if default is not None else key

        translation = lang_dict.get(key)
        if translation is not None:
            return translation
        else:
            logging.warning(
                f"Translation key '{key}' not found for language '{self._current_lang}'."
            )
            return default if default is not None else key


translator = Translator()

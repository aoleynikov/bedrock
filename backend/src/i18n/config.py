from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent.parent.parent / 'translations'
DEFAULT_LOCALE = 'en'
SUPPORTED_LOCALES = ['en', 'es']


def get_translations_path(locale: str) -> Path:
    return TRANSLATIONS_DIR / f'{locale}.yml'

import yaml
from typing import Dict
from src.i18n.config import get_translations_path, DEFAULT_LOCALE, SUPPORTED_LOCALES

_translations_cache: Dict[str, Dict] = {}


def load_translations(locale: str) -> Dict:
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE
    
    if locale in _translations_cache:
        return _translations_cache[locale]
    
    translations_path = get_translations_path(locale)
    
    if not translations_path.exists():
        if locale != DEFAULT_LOCALE:
            return load_translations(DEFAULT_LOCALE)
        return {}
    
    with open(translations_path, 'r', encoding='utf-8') as f:
        translations = yaml.safe_load(f) or {}
    
    _translations_cache[locale] = translations
    return translations


def get_translation(key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
    translations = load_translations(locale)
    
    keys = key.split('.')
    value = translations
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            value = None
            break
    
    if value is None:
        if locale != DEFAULT_LOCALE:
            return get_translation(key, DEFAULT_LOCALE, **kwargs)
        return key
    
    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value
    
    return str(value)

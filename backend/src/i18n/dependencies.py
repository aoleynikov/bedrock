from fastapi import Header
from typing import Optional
from src.i18n.config import DEFAULT_LOCALE, SUPPORTED_LOCALES


def get_locale(accept_language: Optional[str] = Header(None)) -> str:
    if not accept_language:
        return DEFAULT_LOCALE
    
    languages = [lang.strip().split(';')[0].split('-')[0] 
                 for lang in accept_language.split(',')]
    
    for lang in languages:
        if lang in SUPPORTED_LOCALES:
            return lang
    
    return DEFAULT_LOCALE

from fastapi import Request
from src.i18n.loader import get_translation
from src.i18n.config import DEFAULT_LOCALE, SUPPORTED_LOCALES


class Translator:
    def __init__(self, locale: str):
        self.locale = locale
    
    def translate(self, key: str, **kwargs) -> str:
        return get_translation(key, self.locale, **kwargs)
    
    def t(self, key: str, **kwargs) -> str:
        return self.translate(key, **kwargs)


def get_translator(request: Request) -> Translator:
    accept_language = request.headers.get('accept-language', '')
    
    if not accept_language:
        return Translator(DEFAULT_LOCALE)
    
    languages = [lang.strip().split(';')[0].split('-')[0] 
                 for lang in accept_language.split(',')]
    
    for lang in languages:
        if lang in SUPPORTED_LOCALES:
            return Translator(lang)
    
    return Translator(DEFAULT_LOCALE)

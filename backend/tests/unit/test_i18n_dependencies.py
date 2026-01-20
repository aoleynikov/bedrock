import pytest

from src.i18n.config import DEFAULT_LOCALE
from src.i18n.dependencies import get_locale


@pytest.mark.unit
class TestGetLocale:
    def test_returns_default_when_missing(self):
        assert get_locale(None) == DEFAULT_LOCALE

    def test_picks_first_supported_language(self):
        assert get_locale('fr-CA, es;q=0.9, en;q=0.8') == 'es'

    def test_falls_back_when_unsupported(self):
        assert get_locale('fr-CA, de;q=0.9') == DEFAULT_LOCALE

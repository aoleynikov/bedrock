import pytest

from src.exceptions.handlers import translate_validation_message
from src.i18n import config as i18n_config
from src.i18n import loader as i18n_loader
from src.i18n.translator import Translator

@pytest.fixture
def translator(tmp_path, monkeypatch):
    translations_dir = tmp_path / 'translations'
    translations_dir.mkdir()
    translations_file = translations_dir / 'en.yml'
    translations_file.write_text(
        '\n'.join([
            'common:',
            '  validation_error: "Validation error"',
            'validation:',
            '  required: "This field is required"',
            '  string_min_length: "ensure this value has at least {min_length} characters"',
            '  string_max_length: "ensure this value has at most {max_length} characters"',
            '  email_invalid: "value is not a valid email address"',
            '  password_min_length: "Password must be at least 8 characters long"',
            ''
        ]),
        encoding='utf-8'
    )
    monkeypatch.setattr(i18n_config, 'TRANSLATIONS_DIR', translations_dir)
    i18n_loader._translations_cache.clear()
    yield Translator('en')
    i18n_loader._translations_cache.clear()


def test_translate_validation_message_missing(translator: Translator):
    message = translate_validation_message('missing', {}, translator)
    assert message == 'This field is required'


def test_translate_validation_message_string_min_length(translator: Translator):
    message = translate_validation_message('string_too_short', {'min_length': 8}, translator)
    assert message == 'ensure this value has at least 8 characters'


def test_translate_validation_message_string_max_length(translator: Translator):
    message = translate_validation_message('string_too_long', {'max_length': 100}, translator)
    assert message == 'ensure this value has at most 100 characters'


def test_translate_validation_message_email_invalid(translator: Translator):
    message = translate_validation_message('value_error.email', {}, translator)
    assert message == 'value is not a valid email address'


def test_translate_validation_message_password_min_length(translator: Translator):
    message = translate_validation_message('password_min_length', {}, translator)
    assert message == 'Password must be at least 8 characters long'

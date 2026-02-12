import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.base import Llm
from src.llm.openai_llm import OpenAILlm
from src.llm.service import LlmService
from src.llm.template_manager import TemplateManager


@pytest.mark.unit
class TestTemplateManager:
    def test_render_with_template(self, tmp_path):
        (tmp_path / 'hello.j2').write_text('Hello {{ name }}!')
        tm = TemplateManager(base_path=tmp_path)
        result = tm.render('hello', {'name': 'World'})
        assert result == 'Hello World!'

    def test_render_with_j2_suffix(self, tmp_path):
        (tmp_path / 'greet.j2').write_text('Hi {{ who }}')
        tm = TemplateManager(base_path=tmp_path)
        result = tm.render('greet.j2', {'who': 'there'})
        assert result == 'Hi there'

    def test_render_with_empty_data(self, tmp_path):
        (tmp_path / 'static.j2').write_text('Static content')
        tm = TemplateManager(base_path=tmp_path)
        result = tm.render('static', None)
        assert result == 'Static content'

    def test_render_with_empty_dict(self, tmp_path):
        (tmp_path / 'empty.j2').write_text('No vars')
        tm = TemplateManager(base_path=tmp_path)
        result = tm.render('empty', {})
        assert result == 'No vars'


@pytest.mark.unit
class TestLlmService:
    def test_init_assigns_llm_and_template_manager(self):
        llm = MagicMock(spec=Llm)
        tm = MagicMock(spec=TemplateManager)
        service = LlmService(llm=llm, template_manager=tm)
        assert service.llm is llm
        assert service.template_manager is tm


def _make_chat_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = content
    return response


def _make_image_response(b64_data: str) -> MagicMock:
    response = MagicMock()
    response.data = [MagicMock()]
    response.data[0].b64_json = b64_data
    return response


@pytest.mark.unit
@pytest.mark.asyncio
class TestOpenAILlm:
    async def test_process_text_returns_content(self):
        mock_response = _make_chat_response('Hello from model')
        mock_create = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key', model='gpt-4o-mini')
            result = await llm.process_text('Say hello')

        assert result == 'Hello from model'
        mock_create.assert_awaited_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['model'] == 'gpt-4o-mini'
        assert call_kwargs['messages'] == [{'role': 'user', 'content': 'Say hello'}]

    async def test_process_text_with_system_prompt(self):
        mock_response = _make_chat_response('Response')
        mock_create = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key')
            result = await llm.process_text('User msg', system_prompt='You are helpful')

        assert result == 'Response'
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['messages'] == [
            {'role': 'system', 'content': 'You are helpful'},
            {'role': 'user', 'content': 'User msg'},
        ]

    async def test_process_text_returns_empty_when_content_none(self):
        mock_response = _make_chat_response(None)
        mock_create = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key')
            result = await llm.process_text('Prompt')

        assert result == ''

    async def test_process_json_returns_parsed_dict(self):
        payload = {'key': 'value', 'count': 42}
        mock_response = _make_chat_response(json.dumps(payload))
        mock_create = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key')
            result = await llm.process_json('Return JSON')

        assert result == payload
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['response_format'] == {'type': 'json_object'}

    async def test_process_json_with_schema_uses_json_schema_format(self):
        schema = {'type': 'object', 'properties': {'name': {'type': 'string'}}}
        mock_response = _make_chat_response('{"name": "test"}')
        mock_create = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key')
            result = await llm.process_json('Prompt', response_schema=schema)

        assert result == {'name': 'test'}
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['response_format'] == {
            'type': 'json_schema',
            'json_schema': {
                'name': 'response',
                'strict': True,
                'schema': schema,
            },
        }

    async def test_process_json_returns_empty_dict_when_content_empty(self):
        mock_response = _make_chat_response(None)
        mock_create = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key')
            result = await llm.process_json('Prompt')

        assert result == {}

    async def test_generate_image_returns_decoded_bytes(self):
        raw_bytes = b'fake image data'
        b64_data = base64.b64encode(raw_bytes).decode()
        mock_response = _make_image_response(b64_data)
        mock_generate = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.images = MagicMock()
        mock_client.images.generate = mock_generate

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key', image_model='dall-e-3')
            result = await llm.generate_image('A sunset')

        assert result == raw_bytes
        mock_generate.assert_awaited_once_with(
            model='dall-e-3',
            prompt='A sunset',
            n=1,
            response_format='b64_json',
            size='1024x1024',
        )

    async def test_generate_image_raises_when_no_b64_data(self):
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].b64_json = None
        mock_generate = AsyncMock(return_value=mock_response)
        mock_client = MagicMock()
        mock_client.images = MagicMock()
        mock_client.images.generate = mock_generate

        with patch('src.llm.openai_llm.AsyncOpenAI', return_value=mock_client):
            llm = OpenAILlm(api_key='test-key')
            with pytest.raises(ValueError, match='No image data returned from DALL-E'):
                await llm.generate_image('Prompt')

    async def test_init_uses_settings_when_args_omitted(self):
        with patch('src.llm.openai_llm.settings') as mock_settings:
            mock_settings.openai_api_key = 'config-key'
            mock_settings.openai_model = 'config-model'
            mock_settings.openai_image_model = 'config-image-model'
            mock_openai = MagicMock()

            with patch('src.llm.openai_llm.AsyncOpenAI', mock_openai):
                llm = OpenAILlm()

            assert llm._model == 'config-model'
            assert llm._image_model == 'config-image-model'
            mock_openai.assert_called_once_with(api_key='config-key')

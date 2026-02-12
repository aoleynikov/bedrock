import base64
import json
from typing import Optional

from openai import AsyncOpenAI

from src.config import settings
from src.llm.base import Llm


class OpenAILlm(Llm):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        image_model: Optional[str] = None,
    ):
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self._model = model or settings.openai_model
        self._image_model = image_model or settings.openai_image_model

    async def _process_text_impl(
        self, user_prompt: str, system_prompt: str | None = None
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': user_prompt})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        content = response.choices[0].message.content
        return content or ''

    async def _process_json_impl(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        response_schema: dict | None = None,
    ) -> dict:
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': user_prompt})

        kwargs = {'model': self._model, 'messages': messages}

        if response_schema:
            kwargs['response_format'] = {
                'type': 'json_schema',
                'json_schema': {
                    'name': 'response',
                    'strict': True,
                    'schema': response_schema,
                },
            }
        else:
            kwargs['response_format'] = {'type': 'json_object'}

        response = await self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if not content:
            return {}
        return json.loads(content)

    async def _generate_image_impl(self, prompt: str) -> bytes:
        response = await self._client.images.generate(
            model=self._image_model,
            prompt=prompt,
            n=1,
            response_format='b64_json',
            size='1024x1024',
        )
        b64_data = response.data[0].b64_json
        if not b64_data:
            raise ValueError('No image data returned from DALL-E')
        return base64.b64decode(b64_data)

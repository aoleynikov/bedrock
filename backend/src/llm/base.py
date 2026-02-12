from abc import ABC, abstractmethod

from src.logging.logger import get_logger

logger = get_logger(__name__, 'app')


class Llm(ABC):
    async def process_text(
        self, user_prompt: str, system_prompt: str | None = None
    ) -> str:
        logger.debug('LLM process_text prompt', extra={'prompt': user_prompt, 'system_prompt': system_prompt})
        result = await self._process_text_impl(user_prompt, system_prompt)
        logger.debug('LLM process_text result', extra={'result': result})
        return result

    @abstractmethod
    async def _process_text_impl(
        self, user_prompt: str, system_prompt: str | None = None
    ) -> str:
        pass

    async def process_json(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        response_schema: dict | None = None,
    ) -> dict:
        logger.debug('LLM process_json prompt', extra={'prompt': user_prompt, 'system_prompt': system_prompt})
        result = await self._process_json_impl(user_prompt, system_prompt, response_schema)
        logger.debug('LLM process_json result', extra={'result': result})
        return result

    @abstractmethod
    async def _process_json_impl(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        response_schema: dict | None = None,
    ) -> dict:
        pass

    async def generate_image(self, prompt: str) -> bytes:
        logger.debug('LLM generate_image prompt', extra={'prompt': prompt})
        result = await self._generate_image_impl(prompt)
        logger.debug('LLM generate_image result', extra={'prompt': prompt, 'size_bytes': len(result)})
        return result

    @abstractmethod
    async def _generate_image_impl(self, prompt: str) -> bytes:
        pass

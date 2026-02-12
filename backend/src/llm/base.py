from abc import ABC, abstractmethod


class Llm(ABC):
    @abstractmethod
    async def process_text(
        self, user_prompt: str, system_prompt: str | None = None
    ) -> str:
        pass

    @abstractmethod
    async def process_json(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        response_schema: dict | None = None,
    ) -> dict:
        pass

    @abstractmethod
    async def generate_image(self, prompt: str) -> bytes:
        pass

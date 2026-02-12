from abc import ABC

from src.llm.base import Llm
from src.llm.template_manager import TemplateManager


class LlmService(ABC):
    def __init__(self, llm: Llm, template_manager: TemplateManager):
        self.llm = llm
        self.template_manager = template_manager

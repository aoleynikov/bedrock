import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


DEFAULT_PROMPTS_PATH = Path(__file__).resolve().parent.parent.parent / 'templates' / 'prompts'


class TemplateManager:
    def __init__(self, base_path: Path | str | None = None):
        path = Path(base_path) if base_path else DEFAULT_PROMPTS_PATH
        self._env = Environment(
            loader=FileSystemLoader(str(path)),
            auto_reload=os.getenv('ENV', 'local').lower() == 'local',
        )

    def render(self, template_name: str, data: dict | None = None) -> str:
        data = data or {}
        name = f'{template_name}.j2' if not template_name.endswith('.j2') else template_name
        template = self._env.get_template(name)
        return template.render(**data)

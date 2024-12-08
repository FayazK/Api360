from typing import Optional, Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import functools


class TemplateManager:
    def __init__(self, templates_dir: str = "app/templates"):
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Template cache
        self._cache: Dict[str, str] = {}

    @functools.lru_cache(maxsize=100)
    def get_template(self, template_path: str):
        """Get template with caching."""
        return self.env.get_template(template_path)

    def render_prompt(self,
                      template_path: str,
                      variables: Dict[str, Any],
                      cache: bool = True) -> str:
        """Render a prompt template with given variables."""
        try:
            template = self.get_template(template_path)
            rendered = template.render(**variables)

            if cache:
                cache_key = f"{template_path}:{hash(frozenset(variables.items()))}"
                self._cache[cache_key] = rendered

            return rendered
        except Exception as e:
            raise Exception(f"Error rendering template {template_path}: {str(e)}")
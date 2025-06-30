from dataclasses import dataclass

from darq.constants import default_queue_name

DARQ_APP: str = "_darq_app"
DARQ_UI_CONFIG: str = "_darq_ui_config"
DEFAULT_QUEUES = [default_queue_name]


@dataclass
class DarqUIConfig:
    base_path: str
    logs_url: str | None
    queues: list[str]
    embed: bool = False

    def to_dict(self) -> dict:
        return {
            "base_path": self.base_path,
            "logs_url": self.logs_url,
            "embed": self.embed,
            "queues": self.queues,
        }


def join_url(base_url: str, path: str) -> str:
    """Join base url and path maintaining slashes."""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

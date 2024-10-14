from dataclasses import dataclass

DARQ_APP: str = "_darq_app"
DARQ_UI_CONFIG: str = "_darq_ui_config"


@dataclass
class DarqUIConfig:
    base_path: str
    logs_url: str | None
    embed: bool = False

    def to_dict(self) -> dict:
        return {
            "base_path": self.base_path,
            "logs_url": self.logs_url,
            "embed": self.embed,
        }


def join_url(base_url: str, path: str) -> str:
    """Join base url and path maintaining slashes."""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

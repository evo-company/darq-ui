from dataclasses import dataclass

DARQ_APP: str = "_darq_app"
DARQ_UI_CONFIG: str = "_darq_ui_config"


@dataclass
class DarqUIConfig:
    base_path: str
    logs_url: str | None

    def to_dict(self) -> dict:
        return {
            "base_path": self.base_path,
            "logs_url": self.logs_url,
        }

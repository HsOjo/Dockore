from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dockore_token: str = "dev-token-change-me"
    dockore_host: str = "127.0.0.1"
    dockore_port: int = 8000
    dockore_db_url: str = ""
    dockore_data_dir: str = ""
    dockore_cors_origins: str = ""
    dockore_docker_host: str = ""
    dockore_stacks_dir: str = ""
    dockore_backups_dir: str = ""
    dockore_hostname: str = ""
    dockore_terminal_expires: int = 3600

    @property
    def db_url(self) -> str:
        if self.dockore_db_url:
            return self.dockore_db_url
        data_dir = Path(self.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{data_dir}/dockore.db"

    @property
    def data_dir(self) -> Path:
        if self.dockore_data_dir:
            return Path(self.dockore_data_dir)
        path = Path.home() / ".dockore" / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origins(self) -> List[str]:
        if not self.dockore_cors_origins:
            return [
                "http://localhost",
                "http://localhost:1420",
                "http://localhost:5173",
                "http://127.0.0.1",
                "http://127.0.0.1:1420",
                "http://127.0.0.1:5173",
                "tauri://localhost",
                "http://tauri.localhost",
                "https://tauri.localhost",
            ]
        return [o.strip() for o in self.dockore_cors_origins.split(",")]

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent / ".env")
        env_prefix = ""
        case_sensitive = False


settings = Settings()

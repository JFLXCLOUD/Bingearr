"""Application settings, loaded from env (prefix ``BINGEARR_``) or ``.env``."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BINGEARR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Network
    host: str = "0.0.0.0"
    port: int = 9494

    # Storage
    data_dir: Path = Path("data")

    # Auth — empty means "generate + persist on first run".
    api_key: str = ""

    # CORS (dev convenience; the Vite dev server runs on another port).
    cors_origins: list[str] = ["*"]

    # Media-server client tuning
    plex_timeout: int = 30

    @property
    def database_path(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "bingearr.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


settings = Settings()

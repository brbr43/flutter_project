"""Runtime configuration.

STORYVERSE_ROOT points at the machine workspace (on the user's PC: D:\\StoryVerse).
This repo folder `storyverse/` is meant to be copied/synced to `{STORYVERSE_ROOT}\\app`.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_root() -> Path:
    env = os.environ.get("STORYVERSE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    # Dev default: storyverse/../.storyverse-root next to the package, or local data/
    # Prefer a sibling runtime folder under the package so Flutter checkout stays clean.
    package_root = Path(__file__).resolve().parents[1]  # .../storyverse
    return (package_root / "data" / "root").resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STORYVERSE_",
        env_file=".env",
        extra="ignore",
    )

    # Mapped from STORYVERSE_ROOT (env_prefix strips nothing for this override — see property)
    root: Path = Path(".")
    host: str = "127.0.0.1"
    port: int = 8765
    db_filename: str = "storyverse.db"
    # Fake job simulation delay (seconds) for smoke / demo workers
    fake_job_delay_sec: float = 0.25
    api_title: str = "StoryVerse Internal API"
    api_version: str = "0.3.0"

    def model_post_init(self, __context: object) -> None:
        # Allow STORYVERSE_ROOT to set root; also accept bare ROOT via os.environ
        root_env = os.environ.get("STORYVERSE_ROOT")
        if root_env:
            object.__setattr__(self, "root", Path(root_env).expanduser().resolve())
        elif self.root == Path("."):
            object.__setattr__(self, "root", _default_root())
        else:
            object.__setattr__(self, "root", Path(self.root).expanduser().resolve())

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def projects_dir(self) -> Path:
        return self.root / "projects"

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_filename

    @property
    def database_url(self) -> str:
        # Absolute path for SQLite; aiosqlite accepts Path-like via URL
        return f"sqlite+aiosqlite:///{self.db_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

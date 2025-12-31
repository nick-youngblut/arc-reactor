from __future__ import annotations

from pathlib import Path

from dynaconf import Dynaconf

_SETTINGS_PATH = Path(__file__).resolve().parent / "settings.yaml"

settings = Dynaconf(
    envvar_prefix="ARC_REACTOR",
    settings_files=[str(_SETTINGS_PATH)],
    environments=True,
    env_switcher="DYNACONF",
    load_dotenv=True,
)

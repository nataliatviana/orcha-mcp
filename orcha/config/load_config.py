import json
from pathlib import Path
from typing import Any

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from platformdirs import user_config_dir

from orcha.errors import InvalidConfigFileError

APP_NAME = "orcha"
DEFAULT_CONFIG_NAME = "orcha.json"
CONFIG_SCHEMA_NAME = "config_schema.json"

# Linux: ~/.config/orcha
# macOS: ~/Library/Preferences/orcha
# Windows: C:\Users\<user>\AppData\Local\orcha
config_path = Path(user_config_dir(APP_NAME))
FULL_DEFAULT_CONFIG_PATH = config_path / DEFAULT_CONFIG_NAME


def load_config(
    file_path: Path = Path(DEFAULT_CONFIG_NAME),
    dir_path: Path = config_path,
) -> dict[str, Any]:
    # Cria a pasta caso não exista
    dir_path.mkdir(parents=True, exist_ok=True)

    if not file_path.name.endswith(".json"):
        raise InvalidConfigFileError("Config file must have a .json extension")

    config_file = dir_path / file_path

    if not config_file.exists():
        default_config: dict[str, Any] = {}
        config_file.write_text(json.dumps(default_config, indent=2), encoding="utf-8")

    try:
        config = read_json(str(config_file))
        schema = read_json(CONFIG_SCHEMA_NAME)
    except Exception as e:
        raise InvalidConfigFileError(f"Error reading config: {e}") from e

    try:
        validate(instance=config, schema=schema)
        return config
    except ValidationError as e:
        raise InvalidConfigFileError(f"Validation error: {e}") from e


def read_json(path: str) -> dict[str, Any]:
    """Read a JSON file and return a dictionary."""

    with open(path) as f:
        data: Any = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")

    return data

import json
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest
from platformdirs import user_config_dir

from orcha.config.load_config import (
    config_path,
    load_config,
)
from orcha.errors import InvalidConfigFileError

VALID_CONFIG = {
    "llm": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
    }
}


def test_config_path_uses_os_default_dir() -> None:
    """It should use the OS default config directory for the 'orcha' app."""
    assert config_path == Path(user_config_dir("orcha"))


def test_missing_config_file_is_created(tmp_path: Path) -> None:
    """It should create orcha.json with {} when the file does not exist."""
    config_file = tmp_path / "orcha.json"
    assert not config_file.exists()

    with pytest.raises(InvalidConfigFileError):
        load_config(dir_path=tmp_path)

    assert config_file.exists()
    assert json.loads(config_file.read_text()) == {}


def test_missing_config_file_raises_invalid_config_error(tmp_path: Path) -> None:
    """It should raise InvalidConfigFileError when orcha.json is absent."""
    with pytest.raises(InvalidConfigFileError):
        load_config(dir_path=tmp_path)


def test_non_json_extension_raises_error(tmp_path: Path) -> None:
    """It should raise InvalidConfigFileError when the file extension is not .json."""
    with pytest.raises(InvalidConfigFileError) as exc_info:
        load_config(file_path=Path("orcha.txt"), dir_path=tmp_path)

    assert (
        "json" in str(exc_info.value).lower()
        or "extension" in str(exc_info.value).lower()
    )


def test_malformed_json_raises_invalid_config_error(tmp_path: Path) -> None:
    """It should wrap a malformed JSON parse error as InvalidConfigFileError."""
    config_file = tmp_path / "orcha.json"
    config_file.write_text("{invalid json}", encoding="utf-8")

    with pytest.raises(InvalidConfigFileError):
        load_config(dir_path=tmp_path)


def test_json_array_root_raises_invalid_config_error(tmp_path: Path) -> None:
    """It should raise InvalidConfigFileError when the JSON root is not an object."""
    config_file = tmp_path / "orcha.json"
    config_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(InvalidConfigFileError):
        load_config(dir_path=tmp_path)


def test_valid_config_returns_dict(
    make_config: Callable[[Mapping[str, object]], Path],
) -> None:
    """It should return the parsed config as a dict when the file is valid."""
    dir_path = make_config(VALID_CONFIG)

    result = load_config(dir_path=dir_path)

    assert isinstance(result, dict)
    assert result["llm"]["provider"] == "anthropic"
    assert result["llm"]["model"] == "claude-3-5-sonnet-20241022"


def test_schema_validation_error_is_wrapped(
    make_config: Callable[[Mapping[str, object]], Path],
) -> None:
    """It should convert a jsonschema ValidationError into InvalidConfigFileError."""
    from jsonschema.exceptions import ValidationError

    dir_path = make_config({"llm": {"provider": "anthropic"}})  # missing 'model'

    with pytest.raises(InvalidConfigFileError) as exc_info:
        load_config(dir_path=dir_path)

    assert not isinstance(exc_info.value, ValidationError)

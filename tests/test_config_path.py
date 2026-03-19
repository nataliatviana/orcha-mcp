from pathlib import Path

import pytest

from orcha.config.load_config import load_config
from orcha.errors import InvalidConfigFileError


def test_custom_config_path(tmp_path: Path) -> None:
    config_file = tmp_path / "custom.json"

    config_file.write_text(
        """
        {
          "llm": {
            "provider": "anthropic",
            "model": "claude"
          }
        }
        """
    )

    result = load_config(file_path=config_file, dir_path=tmp_path)

    assert result["llm"]["provider"] == "anthropic"


def test_invalid_config_path(tmp_path: Path) -> None:
    with pytest.raises(InvalidConfigFileError):
        load_config(file_path=Path("not-found.json"), dir_path=tmp_path)

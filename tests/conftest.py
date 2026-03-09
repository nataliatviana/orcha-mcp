import json
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest


@pytest.fixture
def make_config(tmp_path: Path) -> Callable[[Mapping[str, object]], Path]:
    """Factory: writes orcha.json to tmp_path with provided content."""

    def _make(content: Mapping[str, object]) -> Path:
        (tmp_path / "orcha.json").write_text(json.dumps(content), encoding="utf-8")
        return tmp_path

    return _make

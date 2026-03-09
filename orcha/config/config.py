from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel

import json
from pathlib import Path


class LocalServerConfig(BaseModel):
    """Configuration for a local MCP server (STDIO)."""

    type: str
    command: List[str]
    enabled: bool = True

    # garangtindo que o environment aceita Record<str, str>
    environment: Optional[Dict[str, str]] = None


class RemoteServerConfig(BaseModel):
    """Configuration for a remote MCP server (HTTP)."""

    type: str
    url: str
    enabled: bool = True
    headers: Optional[Dict[str, str]] = None


class LLMConfig(BaseModel):
    """Configuration for the LLM provider."""

    provider: str
    model: str


class OrchaConfig(BaseModel):
    """Root configuration for orcha."""

    llm: LLMConfig
    mcp_servers: Dict[str, LocalServerConfig | RemoteServerConfig]

   


def load_config(path: str = "orcha.json") -> OrchaConfig:
    """Load configuration from orcha.json."""

    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(
            "Configuration file 'orcha.json' not found. Please create one."
        )

    data = json.loads(config_path.read_text())

    return OrchaConfig.model_validate(data)
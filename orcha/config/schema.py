"""Pydantic models for orcha.json configuration."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider and model configuration."""

    provider: str
    model: str


class LocalServerConfig(BaseModel):
    """Configuration for a local MCP server started via STDIO."""

    type: Literal["local"]
    command: list[str]
    enabled: bool = True
    environment: dict[str, str] = Field(default_factory=dict)


class RemoteServerConfig(BaseModel):
    """Configuration for a remote MCP server accessed via HTTP."""

    type: Literal["remote"]
    url: str
    enabled: bool = True
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: int | None = None


ServerConfig = Annotated[
    LocalServerConfig | RemoteServerConfig,
    Field(discriminator="type"),
]


class OrchaConfig(BaseModel):
    """Root configuration model for orcha.json."""

    llm: LLMConfig
    mcps: dict[str, ServerConfig] = Field(default_factory=dict)

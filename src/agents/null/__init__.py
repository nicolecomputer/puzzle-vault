"""Null agent module."""

from src.agents.null.agent import NullAgent
from src.agents.null.config import NullConfig
from src.agents.registry import AgentInfo

AGENT_INFO = AgentInfo(
    type="null",
    name="Null Agent",
    description="A test agent that does nothing but log that it ran",
    agent_class=NullAgent,
    config_schema=NullConfig,
    ui_hints={},
)

"""Agent registry for discovering and managing agents."""

import importlib
from pathlib import Path
from typing import Any, TypedDict

from pydantic import BaseModel

from src.agents.base_agent import BaseAgent


class AgentPreset(TypedDict):
    """A preset configuration for quickly adding a common source."""

    id: str
    name: str
    short_code: str
    config: dict[str, Any]


class AgentInfo:
    """Information about a registered agent."""

    def __init__(
        self,
        type: str,
        name: str,
        description: str,
        agent_class: type[BaseAgent],
        config_schema: type[BaseModel],
        ui_hints: dict[str, Any] | None = None,
        presets: list[AgentPreset] | None = None,
    ):
        self.type = type
        self.name = name
        self.description = description
        self.agent_class = agent_class
        self.config_schema = config_schema
        self.ui_hints = ui_hints or {}
        self.presets = presets or []


def discover_agents() -> dict[str, AgentInfo]:
    """
    Auto-discover all agent modules in the agents directory.

    Returns:
        Dictionary mapping agent type to agent info
    """
    agents: dict[str, AgentInfo] = {}
    agents_dir = Path(__file__).parent

    for item in agents_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            init_file = item / "__init__.py"
            if init_file.exists():
                try:
                    module = importlib.import_module(f"src.agents.{item.name}")
                    if hasattr(module, "AGENT_INFO"):
                        info: AgentInfo = module.AGENT_INFO
                        agents[info.type] = info
                except ImportError:
                    pass

    return agents


AGENT_REGISTRY = discover_agents()


def get_agent_class(agent_type: str) -> type[BaseAgent] | None:
    """Get the agent class for a given agent type."""
    agent_info = AGENT_REGISTRY.get(agent_type)
    return agent_info.agent_class if agent_info else None


def get_config_schema(agent_type: str) -> type[BaseModel] | None:
    """Get the config schema for a given agent type."""
    agent_info = AGENT_REGISTRY.get(agent_type)
    return agent_info.config_schema if agent_info else None

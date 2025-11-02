"""xword-dl agent module."""

from src.agents.registry import AgentInfo
from src.agents.xword_dl.agent import XwordDlAgent
from src.agents.xword_dl.config import XwordDlConfig

AGENT_INFO = AgentInfo(
    type="xword_dl",
    name="xword-dl Agent",
    description="Downloads puzzles from various outlets using the xword-dl library (USA Today, NYT, LA Times, etc.)",
    agent_class=XwordDlAgent,
    config_schema=XwordDlConfig,
    ui_hints={
        "outlet_keyword": {
            "type": "select",
            "options": [
                {"value": "usa", "label": "USA Today"},
                {"value": "nyt", "label": "New York Times"},
                {"value": "nytm", "label": "New York Times Mini"},
                {"value": "lat", "label": "Los Angeles Times"},
                {"value": "wp", "label": "Washington Post"},
                {"value": "uni", "label": "Universal"},
                {"value": "nd", "label": "Newsday"},
                {"value": "atl", "label": "Atlantic"},
                {"value": "db", "label": "Daily Beast"},
                {"value": "tny", "label": "New Yorker"},
                {"value": "vox", "label": "Vox"},
            ],
        }
    },
)

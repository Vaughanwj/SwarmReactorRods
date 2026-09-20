import json
from datetime import datetime
from pathlib import Path
from typing import Any

from propagation_recorder.domain.models import (
    ActionId,
    ActionKind,
    AgentAction,
    AgentId,
    ArtifactId,
    Consumption,
    Production,
    PropagationGraph,
    Window,
)
from propagation_recorder.domain.services import GraphBuilder


class JsonlGraphStore:
    """Appends each fact as one JSON line; read_window scans the whole file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._builder = GraphBuilder()

    def _append(self, record: dict[str, Any]) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def append_action(self, action: AgentAction) -> None:
        self._append(
            {
                "type": "action",
                "action_id": action.action_id,
                "agent_id": action.agent_id,
                "kind": action.kind.value,
                "timestamp": action.timestamp.isoformat(),
            }
        )

    def append_production(self, production: Production) -> None:
        self._append(
            {"type": "production", "action_id": production.action_id, "artifact_id": production.artifact_id}
        )

    def append_consumption(self, consumption: Consumption) -> None:
        self._append(
            {"type": "consumption", "action_id": consumption.action_id, "artifact_id": consumption.artifact_id}
        )

    def read_window(self, window: Window) -> PropagationGraph:
        actions: list[AgentAction] = []
        productions: list[Production] = []
        consumptions: list[Consumption] = []
        if self._path.exists():
            with self._path.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    kind = rec["type"]
                    if kind == "action":
                        actions.append(
                            AgentAction(
                                ActionId(rec["action_id"]),
                                AgentId(rec["agent_id"]),
                                ActionKind(rec["kind"]),
                                datetime.fromisoformat(rec["timestamp"]),
                            )
                        )
                    elif kind == "production":
                        productions.append(Production(ActionId(rec["action_id"]), ArtifactId(rec["artifact_id"])))
                    elif kind == "consumption":
                        consumptions.append(Consumption(ActionId(rec["action_id"]), ArtifactId(rec["artifact_id"])))
        return self._builder.build(window, actions, productions, consumptions)

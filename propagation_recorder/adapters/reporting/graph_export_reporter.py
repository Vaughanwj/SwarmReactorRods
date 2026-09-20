import json
from pathlib import Path
from typing import Any

from propagation_recorder.domain.models import CouplingEstimate, PropagationGraph


class GraphExportReporter:
    """Exports the graph as structured JSON (no rendering) for a separate visualization step.

    The shape is a handoff contract: {"nodes": [...], "edges": [...]}.
    If a path is given, emit_graph also writes the JSON there; last_export holds the dict.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path is not None else None
        self.last_export: dict[str, Any] | None = None

    @staticmethod
    def to_dict(graph: PropagationGraph) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "action_id": a.action_id,
                    "agent_id": a.agent_id,
                    "kind": a.kind.value,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in graph.actions
            ],
            "edges": [
                {"type": "production", "action_id": p.action_id, "artifact_id": p.artifact_id}
                for p in graph.productions
            ]
            + [
                {"type": "consumption", "action_id": c.action_id, "artifact_id": c.artifact_id}
                for c in graph.consumptions
            ],
        }

    def emit(self, estimate: CouplingEstimate) -> None:
        """Estimates are not part of the graph export; nothing to do."""

    def emit_graph(self, graph: PropagationGraph) -> None:
        self.last_export = self.to_dict(graph)
        if self._path is not None:
            self._path.write_text(json.dumps(self.last_export, indent=2), encoding="utf-8")

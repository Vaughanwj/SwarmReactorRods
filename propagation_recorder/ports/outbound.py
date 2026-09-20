from datetime import datetime
from typing import Any, Protocol

from propagation_recorder.domain.models import (
    AgentAction,
    AgentId,
    ArtifactId,
    Consumption,
    CouplingEstimate,
    Production,
    PropagationGraph,
    Window,
)


class ArtifactIdentity(Protocol):
    def identify(self, payload: bytes | str, context: dict[str, Any]) -> ArtifactId: ...


class GraphStore(Protocol):
    def append_action(self, action: AgentAction) -> None: ...
    def append_production(self, production: Production) -> None: ...
    def append_consumption(self, consumption: Consumption) -> None: ...

    def read_window(self, window: Window) -> PropagationGraph:
        """Actions inside the window, plus the productions and consumptions of those actions."""
        ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class TaskContext(Protocol):
    def declared_inputs(self, agent_id: AgentId) -> set[ArtifactId] | None: ...


class Reporter(Protocol):
    def emit(self, estimate: CouplingEstimate) -> None: ...
    def emit_graph(self, graph: PropagationGraph) -> None: ...

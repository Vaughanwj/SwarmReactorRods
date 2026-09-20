from typing import Protocol

from propagation_recorder.domain.models import (
    AgentAction,
    Consumption,
    CouplingEstimate,
    Production,
    PropagationGraph,
    Window,
)


class ObservationIngest(Protocol):
    def record_action(self, action: AgentAction) -> None: ...
    def record_production(self, production: Production) -> None: ...
    def record_consumption(self, consumption: Consumption) -> None: ...


class CouplingQuery(Protocol):
    def coupling(self, window: Window) -> CouplingEstimate: ...
    def graph_snapshot(self, window: Window) -> PropagationGraph: ...

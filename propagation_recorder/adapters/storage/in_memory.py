from propagation_recorder.domain.models import (
    AgentAction,
    Consumption,
    Production,
    PropagationGraph,
    Window,
)
from propagation_recorder.domain.services import GraphBuilder


class InMemoryGraphStore:
    """Non-persistent GraphStore backed by lists."""

    def __init__(self) -> None:
        self._actions: list[AgentAction] = []
        self._productions: list[Production] = []
        self._consumptions: list[Consumption] = []
        self._builder = GraphBuilder()

    def append_action(self, action: AgentAction) -> None:
        self._actions.append(action)

    def append_production(self, production: Production) -> None:
        self._productions.append(production)

    def append_consumption(self, consumption: Consumption) -> None:
        self._consumptions.append(consumption)

    def read_window(self, window: Window) -> PropagationGraph:
        return self._builder.build(window, self._actions, self._productions, self._consumptions)

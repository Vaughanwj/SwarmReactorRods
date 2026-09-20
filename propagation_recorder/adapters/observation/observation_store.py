from datetime import datetime, timezone

from propagation_recorder.domain.models import (
    AgentAction,
    Consumption,
    CouplingEstimate,
    Production,
    PropagationGraph,
    Window,
)
from propagation_recorder.domain.services import CouplingCalculator
from propagation_recorder.ports.outbound import GraphStore, TaskContext

_ALL_TIME = Window(
    datetime.min.replace(tzinfo=timezone.utc), datetime.max.replace(tzinfo=timezone.utc)
)


class InMemoryObservationStore:
    """Implements ObservationIngest and CouplingQuery over a GraphStore and TaskContext.

    Despite the name it is store-agnostic. Timestamps must be timezone-aware.
    coupling() reads all history so that a production before the window can still
    be resolved, then counts only actions inside the window.
    """

    def __init__(self, store: GraphStore, task_context: TaskContext) -> None:
        self._store = store
        self._task_context = task_context
        self._calculator = CouplingCalculator()

    def record_action(self, action: AgentAction) -> None:
        self._store.append_action(action)

    def record_production(self, production: Production) -> None:
        self._store.append_production(production)

    def record_consumption(self, consumption: Consumption) -> None:
        self._store.append_consumption(consumption)

    def coupling(self, window: Window) -> CouplingEstimate:
        full = self._store.read_window(_ALL_TIME)
        return self._calculator.estimate(full, window, self._task_context.declared_inputs)

    def graph_snapshot(self, window: Window) -> PropagationGraph:
        return self._store.read_window(window)

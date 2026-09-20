from collections.abc import Callable, Iterable

from propagation_recorder.domain.models import (
    AgentAction,
    AgentId,
    ArtifactId,
    Consumption,
    CouplingEstimate,
    PropagationGraph,
    Production,
    Window,
)

# Domain code may not import ports, so the TaskContext port is consumed here as a
# plain callable: agent id -> declared inputs, or None when the system cannot say.
DeclaredInputs = Callable[[AgentId], set[ArtifactId] | None]


class GraphBuilder:
    """Assembles a PropagationGraph for a window from raw stored facts."""

    def build(
        self,
        window: Window,
        actions: Iterable[AgentAction],
        productions: Iterable[Production],
        consumptions: Iterable[Consumption],
    ) -> PropagationGraph:
        in_window = tuple(a for a in actions if window.contains(a.timestamp))
        ids = {a.action_id for a in in_window}
        return PropagationGraph(
            actions=in_window,
            productions=tuple(p for p in productions if p.action_id in ids),
            consumptions=tuple(c for c in consumptions if c.action_id in ids),
        )


class CouplingCalculator:
    """Applies the coupling formula: the fraction of actions in a window that
    consumed another agent's output not accounted for by the declared task.

    Note on producers: the graph passed in must contain the productions to be
    resolved, including those by actions earlier than the window. Only actions
    inside the window are counted. If several actions produced the same artifact,
    the earliest one is taken as its origin.
    """

    def estimate(
        self,
        graph: PropagationGraph,
        window: Window,
        declared_inputs: DeclaredInputs,
    ) -> CouplingEstimate:
        agent_of = {a.action_id: a for a in graph.actions}

        producer: dict[ArtifactId, AgentAction] = {}
        for prod in graph.productions:
            origin = agent_of.get(prod.action_id)
            if origin is None:
                continue
            current = producer.get(prod.artifact_id)
            if current is None or origin.timestamp < current.timestamp:
                producer[prod.artifact_id] = origin

        consumed_by: dict[str, list[ArtifactId]] = {}
        for con in graph.consumptions:
            consumed_by.setdefault(con.action_id, []).append(con.artifact_id)

        total = 0
        coupled = 0
        for action in graph.actions:
            if not window.contains(action.timestamp):
                continue
            total += 1
            if self._is_coupled(action, consumed_by, producer, declared_inputs):
                coupled += 1
        return CouplingEstimate(window=window, coupled_actions=coupled, total_actions=total)

    @staticmethod
    def _is_coupled(
        action: AgentAction,
        consumed_by: dict[str, list[ArtifactId]],
        producer: dict[ArtifactId, AgentAction],
        declared_inputs: DeclaredInputs,
    ) -> bool:
        for artifact_id in consumed_by.get(action.action_id, ()):
            origin = producer.get(artifact_id)
            if origin is None:
                continue  # never resolved to a production: ignored, not an error
            if origin.agent_id == action.agent_id:
                continue  # not cross-agent
            declared = declared_inputs(action.agent_id)
            if declared is not None and artifact_id in declared:
                continue  # accounted for by the task
            return True
        return False


class DispersionCalculator:
    """Stub. Dispersion (the second half of the coal-and-exit signal) is not yet specified."""

    def estimate(self, graph: PropagationGraph, window: Window) -> float:
        raise NotImplementedError("dispersion is not specified for v1")

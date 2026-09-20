from datetime import datetime, timedelta, timezone

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
from propagation_recorder.domain.services import CouplingCalculator, DispersionCalculator

T0 = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
WINDOW = Window(T0, T0 + timedelta(minutes=10))


def act(action_id: str, agent: str, seconds: int) -> AgentAction:
    return AgentAction(
        ActionId(action_id), AgentId(agent), ActionKind.READ, T0 + timedelta(seconds=seconds)
    )


def prod(action_id: str, artifact: str) -> Production:
    return Production(ActionId(action_id), ArtifactId(artifact))


def cons(action_id: str, artifact: str) -> Consumption:
    return Consumption(ActionId(action_id), ArtifactId(artifact))


def none_declared(agent_id: AgentId) -> set[ArtifactId] | None:
    return None


def test_zero_coupling_own_or_no_artifacts() -> None:
    graph = PropagationGraph(
        actions=(act("a1", "x", 0), act("a2", "x", 1), act("a3", "y", 2)),
        productions=(prod("a1", "art"),),
        consumptions=(cons("a2", "art"),),  # same agent consumes its own output
    )
    est = CouplingCalculator().estimate(graph, WINDOW, none_declared)
    assert (est.coupled_actions, est.total_actions, est.k) == (0, 3, 0.0)


def test_full_coupling() -> None:
    graph = PropagationGraph(
        actions=(act("a1", "x", 0), act("a2", "y", 1), act("a3", "x", 2)),
        productions=(prod("a1", "ax"), prod("a2", "ay")),
        consumptions=(cons("a2", "ax"), cons("a3", "ay"), cons("a1", "ay")),
    )
    est = CouplingCalculator().estimate(graph, WINDOW, none_declared)
    assert (est.coupled_actions, est.total_actions, est.k) == (3, 3, 1.0)


def test_task_context_carve_out() -> None:
    graph = PropagationGraph(
        actions=(act("a1", "x", 0), act("a2", "y", 1), act("a3", "z", 2)),
        productions=(prod("a1", "ax"),),
        consumptions=(cons("a2", "ax"), cons("a3", "ax")),
    )

    def declared(agent_id: AgentId) -> set[ArtifactId] | None:
        return {ArtifactId("ax")} if agent_id == "y" else None

    est = CouplingCalculator().estimate(graph, WINDOW, declared)
    assert (est.coupled_actions, est.total_actions) == (1, 3)  # y accounted for, z coupled


def test_declared_set_without_artifact_still_couples() -> None:
    graph = PropagationGraph(
        actions=(act("a1", "x", 0), act("a2", "y", 1)),
        productions=(prod("a1", "ax"),),
        consumptions=(cons("a2", "ax"),),
    )
    est = CouplingCalculator().estimate(graph, WINDOW, lambda _a: {ArtifactId("other")})
    assert est.coupled_actions == 1


def test_consumption_without_production_is_ignored() -> None:
    graph = PropagationGraph(
        actions=(act("a1", "x", 0),),
        productions=(),
        consumptions=(cons("a1", "ghost"),),
    )
    est = CouplingCalculator().estimate(graph, WINDOW, none_declared)
    assert (est.coupled_actions, est.total_actions) == (0, 1)


def test_only_window_actions_counted_but_earlier_productions_resolve() -> None:
    early = Window(T0 - timedelta(hours=1), T0 - timedelta(minutes=30))
    graph = PropagationGraph(
        actions=(
            AgentAction(ActionId("a0"), AgentId("x"), ActionKind.WRITE, early.start),
            act("a1", "y", 1),
        ),
        productions=(prod("a0", "old"),),
        consumptions=(cons("a1", "old"),),
    )
    est = CouplingCalculator().estimate(graph, WINDOW, none_declared)
    assert (est.coupled_actions, est.total_actions) == (1, 1)


def test_empty_window_k_is_zero() -> None:
    est = CouplingCalculator().estimate(PropagationGraph((), (), ()), WINDOW, none_declared)
    assert est.k == 0.0


def test_dispersion_is_a_stub() -> None:
    import pytest

    with pytest.raises(NotImplementedError):
        DispersionCalculator().estimate(PropagationGraph((), (), ()), WINDOW)

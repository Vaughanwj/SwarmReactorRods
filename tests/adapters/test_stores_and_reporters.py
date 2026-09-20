import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from propagation_recorder.adapters.clock.fixed_clock import FixedClock
from propagation_recorder.adapters.clock.system_clock import SystemClock
from propagation_recorder.adapters.reporting.graph_export_reporter import GraphExportReporter
from propagation_recorder.adapters.reporting.stdout_reporter import StdoutReporter
from propagation_recorder.adapters.storage.in_memory import InMemoryGraphStore
from propagation_recorder.adapters.storage.jsonl_store import JsonlGraphStore
from propagation_recorder.adapters.task_context.null_task_context import NullTaskContext
from propagation_recorder.domain.models import (
    ActionId,
    ActionKind,
    AgentAction,
    AgentId,
    ArtifactId,
    Consumption,
    CouplingEstimate,
    Production,
    Window,
)
from propagation_recorder.ports.outbound import GraphStore

T0 = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
WINDOW = Window(T0, T0 + timedelta(minutes=1))


def fill(store: GraphStore) -> None:
    store.append_action(AgentAction(ActionId("a1"), AgentId("x"), ActionKind.WRITE, T0))
    store.append_action(AgentAction(ActionId("late"), AgentId("x"), ActionKind.WRITE, T0 + timedelta(hours=1)))
    store.append_production(Production(ActionId("a1"), ArtifactId("art")))
    store.append_consumption(Consumption(ActionId("late"), ArtifactId("art")))


@pytest.fixture(params=["memory", "jsonl"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> GraphStore:
    if request.param == "memory":
        return InMemoryGraphStore()
    return JsonlGraphStore(tmp_path / "g.jsonl")


def test_read_window_filters_by_timestamp(store: GraphStore) -> None:
    fill(store)
    g = store.read_window(WINDOW)
    assert [a.action_id for a in g.actions] == ["a1"]
    assert len(g.productions) == 1
    assert g.consumptions == ()


def test_export_shape(store: GraphStore, tmp_path: Path) -> None:
    fill(store)
    out = tmp_path / "graph.json"
    rep = GraphExportReporter(out)
    rep.emit_graph(store.read_window(WINDOW))
    data = json.loads(out.read_text())
    assert data == rep.last_export
    assert data["nodes"] == [
        {"action_id": "a1", "agent_id": "x", "kind": "write", "timestamp": T0.isoformat()}
    ]
    assert data["edges"] == [{"type": "production", "action_id": "a1", "artifact_id": "art"}]


def test_stdout_reporter(capsys: pytest.CaptureFixture[str]) -> None:
    rep = StdoutReporter()
    rep.emit(CouplingEstimate(WINDOW, 1, 4))
    rep.emit_graph(InMemoryGraphStore().read_window(WINDOW))
    out = capsys.readouterr().out
    assert "k=0.250" in out and "coupled=1" in out and "total=4" in out
    assert "0 nodes, 0 edges" in out


def test_clocks() -> None:
    assert FixedClock(T0).now() == T0 == FixedClock(T0).now()
    seq = FixedClock([T0, T0 + timedelta(seconds=1)])
    assert seq.now() == T0
    assert seq.now() == T0 + timedelta(seconds=1)
    with pytest.raises(RuntimeError):
        seq.now()
    assert SystemClock().now().tzinfo is not None


def test_null_task_context() -> None:
    assert NullTaskContext().declared_inputs(AgentId("x")) is None

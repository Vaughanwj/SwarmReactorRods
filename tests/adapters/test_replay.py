from pathlib import Path

import pytest

from propagation_recorder.adapters.identity.exact_match import ExactMatchArtifactIdentity
from propagation_recorder.adapters.observation.observation_store import InMemoryObservationStore
from propagation_recorder.adapters.replay.jsonl_replay import JsonlReplayAdapter, ReplayError
from propagation_recorder.adapters.storage.in_memory import InMemoryGraphStore
from propagation_recorder.adapters.task_context.null_task_context import NullTaskContext
from propagation_recorder.domain.models import (
    AgentAction,
    Consumption,
    Production,
    Window,
)
from datetime import datetime, timezone

FIXTURE = Path(__file__).parent.parent / "fixtures" / "small_log.jsonl"


class RecordingIngest:
    def __init__(self) -> None:
        self.actions: list[AgentAction] = []
        self.productions: list[Production] = []
        self.consumptions: list[Consumption] = []

    def record_action(self, action: AgentAction) -> None:
        self.actions.append(action)

    def record_production(self, production: Production) -> None:
        self.productions.append(production)

    def record_consumption(self, consumption: Consumption) -> None:
        self.consumptions.append(consumption)


def test_drives_all_three_ingest_methods() -> None:
    ingest = RecordingIngest()
    n = JsonlReplayAdapter(ExactMatchArtifactIdentity()).replay(FIXTURE, ingest)
    assert n == 6
    assert [a.action_id for a in ingest.actions] == ["a1", "a2", "a3"]
    assert len(ingest.productions) == 1
    assert len(ingest.consumptions) == 2
    # verbatim reuse resolves to the same artifact; the paraphrase does not
    assert ingest.consumptions[0].artifact_id == ingest.productions[0].artifact_id
    assert ingest.consumptions[1].artifact_id != ingest.productions[0].artifact_id


def test_end_to_end_coupling_from_fixture() -> None:
    store = InMemoryObservationStore(InMemoryGraphStore(), NullTaskContext())
    JsonlReplayAdapter(ExactMatchArtifactIdentity()).replay(FIXTURE, store)
    window = Window(
        datetime(2026, 9, 20, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 20, 11, 0, tzinfo=timezone.utc),
    )
    est = store.coupling(window)
    assert (est.coupled_actions, est.total_actions) == (1, 3)


def test_undeclared_action_id_raises(tmp_path: Path) -> None:
    log = tmp_path / "bad.jsonl"
    log.write_text('{"event": "consumption", "action_id": "nope", "payload": "x", "context": {}}\n')
    with pytest.raises(ReplayError, match="undeclared action_id 'nope'"):
        JsonlReplayAdapter(ExactMatchArtifactIdentity()).replay(log, RecordingIngest())


def test_malformed_lines_raise(tmp_path: Path) -> None:
    adapter = JsonlReplayAdapter(ExactMatchArtifactIdentity())
    for i, text in enumerate(["not json", '{"event": "bogus"}', '{"event": "action"}']):
        log = tmp_path / f"m{i}.jsonl"
        log.write_text(text + "\n")
        with pytest.raises(ReplayError, match="line 1"):
            adapter.replay(log, RecordingIngest())

"""Produces the single JSON data file the visualization (viz.html) embeds.

This is item 2 of spock-return-brief.md's suggested next stage: "Build the
visualization against the graph export JSON." The graph export shape itself
(GraphExportReporter.to_dict) is the library's frozen contract and is used
here unchanged. What this script adds on top, for the visualization only, is
a per-edge classification (same-agent / accounted / coupled / unresolved),
computed by re-deriving the same producer-resolution and cross-agent check
CouplingCalculator uses internally, from the graph's own public fields
(actions, productions, consumptions) plus the same declared_inputs callable.

This is deliberately not a change to the library or a new library-exposed
method: CouplingCalculator returns an aggregate CouplingEstimate by design
(see its docstring and the known-limitations note in spock-return-brief.md:
"coupling is per-action, binary... the number of coupled edges is not
exposed"). Classifying individual edges is a visualization concern, scoped
to this demo, the same way DeclaredTaskContext is.

Run: python demo/export_visualization_data.py
Writes: demo/logs/viz_data.json
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).parent))

from declared_task_context import DeclaredTaskContext
from scenario_payloads import DRAFT, PLAN, RESEARCH_NOTES

from propagation_recorder.adapters.identity.exact_match import ExactMatchArtifactIdentity
from propagation_recorder.adapters.observation.observation_store import InMemoryObservationStore
from propagation_recorder.adapters.reporting.graph_export_reporter import GraphExportReporter
from propagation_recorder.adapters.replay.jsonl_replay import JsonlReplayAdapter
from propagation_recorder.adapters.storage.in_memory import InMemoryGraphStore
from propagation_recorder.adapters.task_context.null_task_context import NullTaskContext
from propagation_recorder.domain.models import (
    AgentAction,
    AgentId,
    ArtifactId,
    PropagationGraph,
    Window,
)
from propagation_recorder.domain.services import DeclaredInputs
from propagation_recorder.ports.outbound import TaskContext

LOGS_DIR = Path(__file__).parent / "logs"

WINDOW = Window(
    datetime(2026, 9, 20, 9, 59, 0, tzinfo=timezone.utc),
    datetime(2026, 9, 20, 10, 11, 0, tzinfo=timezone.utc),
)

EdgeClass = Literal["same-agent", "accounted", "coupled", "unresolved"]


@dataclass(frozen=True)
class ClassifiedConsumption:
    action_id: str
    artifact_id: str
    producer_action_id: str | None
    classification: EdgeClass


def classify_consumptions(
    graph: PropagationGraph, declared_inputs: DeclaredInputs
) -> list[ClassifiedConsumption]:
    """Mirrors CouplingCalculator._is_coupled's logic, per edge instead of
    aggregated, for the visualization only. See module docstring."""
    agent_of = {a.action_id: a for a in graph.actions}

    producer: dict[str, AgentAction] = {}
    for prod in graph.productions:
        origin = agent_of.get(prod.action_id)
        if origin is None:
            continue
        current = producer.get(prod.artifact_id)
        if current is None or origin.timestamp < current.timestamp:
            producer[prod.artifact_id] = origin

    classified = []
    for con in graph.consumptions:
        consumer = agent_of[con.action_id]
        origin = producer.get(con.artifact_id)
        if origin is None:
            classification: EdgeClass = "unresolved"
            producer_action_id = None
        elif origin.agent_id == consumer.agent_id:
            classification = "same-agent"
            producer_action_id = origin.action_id
        else:
            declared = declared_inputs(consumer.agent_id)
            if declared is not None and con.artifact_id in declared:
                classification = "accounted"
            else:
                classification = "coupled"
            producer_action_id = origin.action_id
        classified.append(
            ClassifiedConsumption(con.action_id, con.artifact_id, producer_action_id, classification)
        )
    return classified


def declared_task_context() -> DeclaredTaskContext:
    identity = ExactMatchArtifactIdentity()
    return DeclaredTaskContext(
        {
            AgentId("agent-researcher"): {ArtifactId(identity.identify(PLAN, {}))},
            AgentId("agent-writer"): {ArtifactId(identity.identify(RESEARCH_NOTES, {}))},
            AgentId("agent-editor"): {ArtifactId(identity.identify(DRAFT, {}))},
        }
    )


def build_view(log_path: Path, task_context: TaskContext) -> dict[str, object]:
    store = InMemoryGraphStore()
    observation = InMemoryObservationStore(store, task_context)
    JsonlReplayAdapter(ExactMatchArtifactIdentity()).replay(log_path, observation)
    estimate = observation.coupling(WINDOW)
    graph = observation.graph_snapshot(WINDOW)
    export = GraphExportReporter.to_dict(graph)

    classified = classify_consumptions(graph, task_context.declared_inputs)
    consumption_edges = [
        {
            "action_id": c.action_id,
            "artifact_id": c.artifact_id,
            "producer_action_id": c.producer_action_id,
            "classification": c.classification,
        }
        for c in classified
    ]
    coupled_action_ids = sorted(
        {c.action_id for c in classified if c.classification == "coupled"}
    )

    return {
        "nodes": export["nodes"],
        "production_edges": [e for e in export["edges"] if e["type"] == "production"],
        "consumption_edges": consumption_edges,
        "estimate": {
            "k": estimate.k,
            "coupled_actions": estimate.coupled_actions,
            "total_actions": estimate.total_actions,
        },
        "coupled_action_ids": coupled_action_ids,
    }


def main() -> None:
    logs = {
        "benign": LOGS_DIR / "benign.jsonl",
        "steered": LOGS_DIR / "steered.jsonl",
        "steered_paraphrased": LOGS_DIR / "steered_paraphrased.jsonl",
    }
    missing = [name for name, path in logs.items() if not path.exists()]
    if missing:
        raise SystemExit("Run demo/build_logs.py first to generate the event logs.")

    declared = declared_task_context()
    null = NullTaskContext()

    data: dict[str, object] = {
        scenario: {
            "NullTaskContext": build_view(path, null),
            "DeclaredTaskContext": build_view(path, declared),
        }
        for scenario, path in logs.items()
    }
    data["window"] = {"start": WINDOW.start.isoformat(), "end": WINDOW.end.isoformat()}

    out_path = LOGS_DIR / "viz_data.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

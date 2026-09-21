"""Runs both demonstration logs through the library and prints a comparison.

This is the part of the "suggested next stage" from spock-return-brief.md that
answers item 4 directly, instead of just declaring an answer: it runs the same
benign and steered logs under NullTaskContext (the library's shipped default,
which cannot say what any agent's job is) and under DeclaredTaskContext (the
scenario-specific adapter in this directory, which can). The four resulting
numbers are the actual demonstration of why TaskContext matters, not an
assertion about it.

Usage: python demo/run_scenario.py
(Run demo/build_logs.py first if demo/logs/*.jsonl don't exist yet.)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from declared_task_context import DeclaredTaskContext
from scenario_payloads import DRAFT, PLAN, RESEARCH_NOTES

from propagation_recorder.adapters.identity.exact_match import ExactMatchArtifactIdentity
from propagation_recorder.adapters.observation.observation_store import InMemoryObservationStore
from propagation_recorder.adapters.reporting.graph_export_reporter import GraphExportReporter
from propagation_recorder.adapters.replay.jsonl_replay import JsonlReplayAdapter
from propagation_recorder.adapters.storage.in_memory import InMemoryGraphStore
from propagation_recorder.adapters.task_context.null_task_context import NullTaskContext
from propagation_recorder.domain.models import AgentId, ArtifactId, CouplingEstimate, Window
from propagation_recorder.ports.outbound import TaskContext

LOGS_DIR = Path(__file__).parent / "logs"

# The window is wide enough to cover every action in either log (10:00:00 to
# 10:09:30) with margin; it is not "all time" because a real report is always
# run against some bounded window and the demo should reflect that.
WINDOW = Window(
    datetime(2026, 9, 20, 9, 59, 0, tzinfo=timezone.utc),
    datetime(2026, 9, 20, 10, 11, 0, tzinfo=timezone.utc),
)


def declared_task_context() -> DeclaredTaskContext:
    """The hand-off mapping for the *legitimate* pipeline, identical for both
    scenarios. Deliberately says nothing about agent-injector: a real
    deployment's task declarations describe the work agents were assigned,
    not the attacks that might target them, so the injected strand in the
    steered log is unaccounted here precisely because nobody declared it,
    not because this mapping was written to catch it.
    """
    identity = ExactMatchArtifactIdentity()
    return DeclaredTaskContext(
        {
            AgentId("agent-researcher"): {ArtifactId(identity.identify(PLAN, {}))},
            AgentId("agent-writer"): {ArtifactId(identity.identify(RESEARCH_NOTES, {}))},
            AgentId("agent-editor"): {ArtifactId(identity.identify(DRAFT, {}))},
        }
    )


def run(log_path: Path, task_context: TaskContext) -> tuple[CouplingEstimate, dict[str, Any]]:
    store = InMemoryGraphStore()
    observation = InMemoryObservationStore(store, task_context)
    JsonlReplayAdapter(ExactMatchArtifactIdentity()).replay(log_path, observation)
    estimate = observation.coupling(WINDOW)
    graph = observation.graph_snapshot(WINDOW)
    export = GraphExportReporter()
    export.emit_graph(graph)
    assert export.last_export is not None  # emit_graph just set it
    return estimate, export.last_export


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

    results = {}
    for scenario, log_path in logs.items():
        results[(scenario, "NullTaskContext")] = run(log_path, NullTaskContext())
        results[(scenario, "DeclaredTaskContext")] = run(log_path, declared)

    print(f"{'scenario':<20} {'TaskContext':<22} {'coupled':>7} {'total':>7} {'k':>6}")
    for (scenario, tc_name), (estimate, _) in results.items():
        print(
            f"{scenario:<20} {tc_name:<22} {estimate.coupled_actions:>7} "
            f"{estimate.total_actions:>7} {estimate.k:>6.2f}"
        )
    print(
        "\nsteered_paraphrased: under exact-match identity, the three "
        "paraphrased consumptions (b2/b3/b4) never resolve to the artifact "
        "the injector produced, so they add zero coupled actions -- the "
        "coupled-action set is exactly {a2, a3, a4}, identical to benign, "
        "under both TaskContexts. This is the known limitation working as "
        "documented, not a bug. k itself is not identical to benign's (it's "
        "diluted by four extra, uncoupled actions in the denominator: 0.30 "
        "vs 0.50 under Null, 0.00 vs 0.00 under Declared) -- the thing to "
        "read here is the zero contribution from the injected strand, not "
        "the k value. The exact-vs-fuzzy comparison this sets up waits on "
        "FuzzyArtifactIdentity (Spock's, per delayed-critical-handoff.md)."
    )

    for (scenario, tc_name), (_, export) in results.items():
        out_path = LOGS_DIR / f"{scenario}_{tc_name}_graph.json"
        out_path.write_text(json.dumps(export, indent=2), encoding="utf-8")
    print(f"\nGraph exports written to {LOGS_DIR}")


if __name__ == "__main__":
    main()

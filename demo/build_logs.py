"""Generates the two demonstration event logs against the schema in
docs/build-brief.md, and nothing else. Run once (or whenever the scenario
changes) to (re)write demo/logs/benign.jsonl and demo/logs/steered.jsonl.

Both logs share an identical legitimate backbone: a four-agent pipeline
(planner -> researcher -> writer -> editor) where each agent's hand-off to
the next is exactly what that agent's task declares it should read. The
steered log adds one extra strand on top of that same backbone: an
"agent-injector" that plants an instruction nobody's task called for, which
the researcher, writer and editor agents each pick up verbatim and act on.
Keeping the backbone identical between the two logs is deliberate — it is
what lets run_scenario.py show that the elevated coupling in the steered log
comes specifically from the injected strand, not from the pipeline itself
looking different.

Payload strings are exact-match, per ExactMatchArtifactIdentity: a production
and a consumption resolve to the same artifact only if the payload bytes are
identical. That is why every hand-off below reuses a payload constant from
scenario_payloads.py rather than re-typing a "close enough" string.
"""

import json
from pathlib import Path
from typing import Any

from scenario_payloads import (
    DRAFT,
    FINAL,
    INJECTED_INSTRUCTION,
    PLAN,
    QA_PING,
    RESEARCH_NOTES,
)

LOGS_DIR = Path(__file__).parent / "logs"

Event = dict[str, Any]


def action(action_id: str, agent_id: str, kind: str, timestamp: str) -> Event:
    return {"event": "action", "action_id": action_id, "agent_id": agent_id, "kind": kind, "timestamp": timestamp}


def production(action_id: str, payload: str) -> Event:
    return {"event": "production", "action_id": action_id, "payload": payload, "context": {}}


def consumption(action_id: str, payload: str) -> Event:
    return {"event": "consumption", "action_id": action_id, "payload": payload, "context": {}}


def write_log(path: Path, events: list[Event]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def legitimate_backbone() -> list[Event]:
    return [
        # Planner writes the plan.
        action("a1", "agent-planner", "write", "2026-09-20T10:00:00Z"),
        production("a1", PLAN),
        # Planner re-reads its own note before moving on. Self-consumption,
        # never counts as coupling regardless of TaskContext.
        action("a1r", "agent-planner", "read", "2026-09-20T10:00:30Z"),
        consumption("a1r", PLAN),
        # Researcher's assigned task is to read the plan and produce research.
        # This is the kind of cross-agent read a TaskContext should declare.
        action("a2", "agent-researcher", "write", "2026-09-20T10:02:00Z"),
        consumption("a2", PLAN),
        production("a2", RESEARCH_NOTES),
        # Writer's assigned task is to read the research and produce a draft.
        action("a3", "agent-writer", "write", "2026-09-20T10:05:00Z"),
        consumption("a3", RESEARCH_NOTES),
        production("a3", DRAFT),
        # Editor's assigned task is to read the draft and produce the final.
        action("a4", "agent-editor", "write", "2026-09-20T10:08:00Z"),
        consumption("a4", DRAFT),
        production("a4", FINAL),
        # Unrelated padding action: a QA heartbeat with no cross-agent read at
        # all, so it can never be coupled under any TaskContext.
        action("qa1", "agent-qa", "tool_call", "2026-09-20T10:09:30Z"),
        production("qa1", QA_PING),
    ]


def injected_strand() -> list[Event]:
    return [
        # A compromised or adversarial agent plants an instruction that is not
        # part of anyone's declared task. Its own action has no consumption
        # edge, so it is never itself "coupled" by this metric -- it is the
        # origin, not something caused by another agent's output.
        action("b1", "agent-injector", "write", "2026-09-20T10:01:00Z"),
        production("b1", INJECTED_INSTRUCTION),
        # Researcher, writer and editor each pick up the exact injected text
        # in a tool call and act on it. None of their declared tasks mention
        # agent-injector, so under a correctly-declared TaskContext all three
        # are unaccounted cross-agent reads.
        action("b2", "agent-researcher", "tool_call", "2026-09-20T10:03:00Z"),
        consumption("b2", INJECTED_INSTRUCTION),
        action("b3", "agent-writer", "tool_call", "2026-09-20T10:06:00Z"),
        consumption("b3", INJECTED_INSTRUCTION),
        action("b4", "agent-editor", "tool_call", "2026-09-20T10:09:00Z"),
        consumption("b4", INJECTED_INSTRUCTION),
    ]


def main() -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    write_log(LOGS_DIR / "benign.jsonl", legitimate_backbone())
    write_log(LOGS_DIR / "steered.jsonl", legitimate_backbone() + injected_strand())
    print(f"Wrote {LOGS_DIR / 'benign.jsonl'} and {LOGS_DIR / 'steered.jsonl'}")


if __name__ == "__main__":
    main()

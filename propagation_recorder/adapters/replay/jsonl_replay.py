import json
from datetime import datetime
from pathlib import Path
from typing import Any

from propagation_recorder.domain.models import (
    ActionId,
    ActionKind,
    AgentAction,
    AgentId,
    Consumption,
    Production,
)
from propagation_recorder.ports.inbound import ObservationIngest
from propagation_recorder.ports.outbound import ArtifactIdentity


class ReplayError(ValueError):
    """Raised when an event log is malformed."""


class JsonlReplayAdapter:
    """Reads a JSONL event log and drives an ObservationIngest from it.

    Events: "action", "production", "consumption" (see docs/build-brief.md for the
    schema). production/consumption must reference an action_id introduced by an
    earlier action line. Payloads go through the ArtifactIdentity; a consumption
    that matches no production is still recorded and simply never resolves.
    """

    def __init__(self, identity: ArtifactIdentity) -> None:
        self._identity = identity

    def replay(self, path: str | Path, ingest: ObservationIngest) -> int:
        """Replay the file; returns the number of events processed."""
        known: set[str] = set()
        count = 0
        with Path(path).open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ReplayError(f"line {lineno}: invalid JSON: {e}") from e
                if not isinstance(rec, dict):
                    raise ReplayError(f"line {lineno}: expected a JSON object")
                self._handle(lineno, rec, known, ingest)
                count += 1
        return count

    def _handle(self, lineno: int, rec: dict[str, Any], known: set[str], ingest: ObservationIngest) -> None:
        event = rec.get("event")
        try:
            if event == "action":
                action = AgentAction(
                    ActionId(rec["action_id"]),
                    AgentId(rec["agent_id"]),
                    ActionKind(rec["kind"]),
                    datetime.fromisoformat(rec["timestamp"]),
                )
                known.add(action.action_id)
                ingest.record_action(action)
            elif event in ("production", "consumption"):
                action_id = rec["action_id"]
                if action_id not in known:
                    raise ReplayError(
                        f"line {lineno}: {event} references undeclared action_id {action_id!r}"
                    )
                artifact_id = self._identity.identify(rec["payload"], rec.get("context", {}))
                if event == "production":
                    ingest.record_production(Production(ActionId(action_id), artifact_id))
                else:
                    ingest.record_consumption(Consumption(ActionId(action_id), artifact_id))
            else:
                raise ReplayError(f"line {lineno}: unknown event type {event!r}")
        except KeyError as e:
            raise ReplayError(f"line {lineno}: missing field {e}") from e
        except ReplayError:
            raise
        except ValueError as e:
            raise ReplayError(f"line {lineno}: {e}") from e

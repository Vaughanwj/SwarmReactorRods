# Build brief: propagation recorder library

Self-contained. Written on the assumption this is handed to a fresh Claude
Code session with no access to the claude.ai project this came from. Everything
needed is inline below.

## What this is, one paragraph

A small library that watches a multi-agent system and answers one question:
for a given agent action, which other agent's output, if any, caused it. It
does this by recording two kinds of fact, what an action produced and what an
action consumed, and computing what fraction of actions in a time window were
caused by another agent's output rather than accounted for by the task each
agent was actually assigned. That fraction is called k. This library measures.
It does not decide, intervene, block, or classify anything as malicious.

## Scope, explicit

Build: the domain model, the ports, the coupling calculator, the adapters
listed below, unit tests. Nothing else.

Do not build: a live framework adapter for any specific agent framework, the
demonstration scenario data (benign/steered logs), any rendered visualization,
any intervention or blocking logic, any baseline-learning or anomaly-detection
model, any semantic or fuzzy artifact matching, a README narrative beyond how
to install and run the tests. All of that belongs to a different piece of this
project and building it here would be wasted and possibly contradictory work.

Language: Python 3.12 or later. Package manager and layout tooling your
choice (poetry or uv are both fine), document whichever you pick in a short
line at the top of `pyproject.toml`. Testing: pytest. Type hints throughout;
aim for a clean `mypy --strict` pass but don't burn excessive time chasing the
last few edge cases if it costs more than it's worth.

Architecture: hexagonal, strictly. The domain package has zero imports from
ports or adapters. Ports are defined as `typing.Protocol` classes in their own
package and import only the domain. Adapters implement ports, import the
domain and the port they implement, and are never imported by the domain or
by ports. If you find yourself importing an adapter from inside the domain to
make something convenient, stop, that's the boundary being violated, restructure
instead.

## Repository layout

```
propagation_recorder/
    domain/
        models.py
        services.py
    ports/
        inbound.py
        outbound.py
    adapters/
        identity/
            exact_match.py
        storage/
            in_memory.py
            jsonl_store.py
        clock/
            system_clock.py
            fixed_clock.py
        task_context/
            null_task_context.py
        reporting/
            stdout_reporter.py
            graph_export_reporter.py
        replay/
            jsonl_replay.py
tests/
    domain/
    adapters/
    fixtures/
pyproject.toml
README.md
```

Package name `propagation_recorder` is a placeholder, the repo name is still
undecided upstream, rename freely, just keep internal imports consistent.

## Domain model, exact

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NewType

ActionId = NewType("ActionId", str)
AgentId = NewType("AgentId", str)
ArtifactId = NewType("ArtifactId", str)


class ActionKind(str, Enum):
    READ = "read"
    WRITE = "write"
    TOOL_CALL = "tool_call"
    SPAWN = "spawn"


@dataclass(frozen=True)
class AgentAction:
    action_id: ActionId
    agent_id: AgentId
    kind: ActionKind
    timestamp: datetime


@dataclass(frozen=True)
class Production:
    action_id: ActionId
    artifact_id: ArtifactId


@dataclass(frozen=True)
class Consumption:
    action_id: ActionId
    artifact_id: ArtifactId


@dataclass(frozen=True)
class Window:
    start: datetime
    end: datetime

    def contains(self, ts: datetime) -> bool:
        return self.start <= ts <= self.end


@dataclass(frozen=True)
class CouplingEstimate:
    window: Window
    coupled_actions: int
    total_actions: int

    @property
    def k(self) -> float:
        if self.total_actions == 0:
            return 0.0
        return self.coupled_actions / self.total_actions


@dataclass(frozen=True)
class PropagationGraph:
    actions: tuple[AgentAction, ...]
    productions: tuple[Production, ...]
    consumptions: tuple[Consumption, ...]
```

Note deliberately: the domain model never stores artifact payloads or
content. Identity resolution (deciding two things are "the same artifact") is
entirely the job of the `ArtifactIdentity` port, at the boundary. The domain
only ever sees an already-resolved `ArtifactId`. Do not add a `payload` field
to any domain type, that would leak an adapter concern into the domain.

## Coupling formula, exact, do not improvise a different one

For a given `Window`:

1. Take all `AgentAction`s whose `timestamp` falls inside the window.
2. For each such action, find its `Consumption` edges (matching `action_id`).
3. For each consumption edge, find the `Production` edge with the same
   `artifact_id` and read off that production's action's `agent_id` (the
   producing agent). If no matching production exists in the graph at all,
   that consumption edge is ignored, it never resolved to anything, this is
   expected and not an error.
4. A consumption edge is **cross-agent** if the producing agent's id differs
   from the consuming action's agent id.
5. For each cross-agent edge, call `TaskContext.declared_inputs(consuming
   agent_id)`. If it returns a set and the artifact id is a member, the edge
   is **accounted for** and does not count as coupling. If it returns `None`,
   or the artifact id is not in the returned set, the edge **counts as
   coupling**.
6. An action is **coupled** if it has at least one cross-agent, unaccounted
   consumption edge.
7. `coupled_actions` = count of coupled actions in the window.
   `total_actions` = count of all actions in the window (coupled or not).
   `k` = `coupled_actions / total_actions`, or `0.0` if `total_actions == 0`.

This is the entire algorithm. It is intentionally simple arithmetic over a
graph, not a model, not a heuristic with tunable weights. If a design
decision seems to call for a threshold, a weight, or a learned parameter,
that's a sign the decision belongs in a different port (most likely
`TaskContext` or a future `DispersionCalculator`), not folded into this
formula.

`DispersionCalculator` is a stub for v1: define the class and its intended
signature (`estimate(graph: PropagationGraph, window: Window) -> float`, or
similar, use your judgment on the exact signature) but have it raise
`NotImplementedError`. Do not attempt to implement dispersion, it isn't
specified yet.

## Ports, exact

```python
from typing import Protocol, Optional


class ObservationIngest(Protocol):
    def record_action(self, action: AgentAction) -> None: ...
    def record_production(self, production: Production) -> None: ...
    def record_consumption(self, consumption: Consumption) -> None: ...


class CouplingQuery(Protocol):
    def coupling(self, window: Window) -> CouplingEstimate: ...
    def graph_snapshot(self, window: Window) -> PropagationGraph: ...


class ArtifactIdentity(Protocol):
    def identify(self, payload: bytes | str, context: dict) -> ArtifactId: ...


class GraphStore(Protocol):
    def append_action(self, action: AgentAction) -> None: ...
    def append_production(self, production: Production) -> None: ...
    def append_consumption(self, consumption: Consumption) -> None: ...
    def read_window(self, window: Window) -> PropagationGraph: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class TaskContext(Protocol):
    def declared_inputs(self, agent_id: AgentId) -> Optional[set[ArtifactId]]: ...


class Reporter(Protocol):
    def emit(self, estimate: CouplingEstimate) -> None: ...
    def emit_graph(self, graph: PropagationGraph) -> None: ...
```

`GraphBuilder` and `CouplingCalculator` are domain services (plain classes,
not ports) that sit behind `CouplingQuery`: `GraphBuilder` assembles a
`PropagationGraph` from a `GraphStore`'s window read, `CouplingCalculator`
applies the formula above to produce a `CouplingEstimate`. A concrete
adapter implementing `ObservationIngest` and `CouplingQuery` together
(call it `InMemoryObservationStore` or similar) wires a `GraphStore` and a
`TaskContext` behind these two ports. Use your judgment on exact class
boundaries here as long as the domain/ports/adapters import discipline holds.

## Adapters to implement

- **`ExactMatchArtifactIdentity`**: `identify()` returns a stable hash (sha256
  hex digest is fine) of the payload as UTF-8 bytes, ignoring `context` for
  v1. Put a docstring on this class stating plainly that it will not match
  paraphrased or summarized content, that's a known, intentional limitation,
  not a bug to work around.
- **`InMemoryGraphStore`**: lists or similar in-memory structures. No
  persistence.
- **`JsonlGraphStore`**: appends each recorded fact as one JSON line to a
  file. `read_window` scans the file and filters by timestamp. No indexing or
  performance work needed for v1.
- **`SystemClock`**: wraps `datetime.now(timezone.utc)`.
- **`FixedClock`**: constructed with either a single fixed `datetime` or an
  iterable of timestamps to hand out in sequence, needed for deterministic
  tests and replay.
- **`NullTaskContext`**: `declared_inputs` always returns `None`.
- **`StdoutReporter`**: `emit` prints a short human-readable line with the
  window, `k`, `coupled_actions`, `total_actions`. `emit_graph` can print a
  one-line summary (node and edge counts), it doesn't need to render anything.
- **`GraphExportReporter`**: `emit_graph` writes structured JSON, not a
  rendered image, to a file or returns a dict, matching this shape:

  ```json
  {
    "nodes": [
      {"action_id": "...", "agent_id": "...", "kind": "read", "timestamp": "..."}
    ],
    "edges": [
      {"type": "production", "action_id": "...", "artifact_id": "..."},
      {"type": "consumption", "action_id": "...", "artifact_id": "..."}
    ]
  }
  ```

  This is the handoff format to a separate visualization step that is not
  part of this build. Keep the shape exactly as above, another piece of work
  depends on parsing it.

- **`JsonlReplayAdapter`**: reads a JSONL event log (schema below) and drives
  an `ObservationIngest` implementation from it. This is the adapter the
  demonstration will actually run through, get it solid and well-tested.

## Event log schema (interface contract, do not change without flagging it)

One JSON object per line. Three event types:

```json
{"event": "action", "action_id": "a1", "agent_id": "agent-1", "kind": "write", "timestamp": "2026-09-20T10:00:00Z"}
{"event": "production", "action_id": "a1", "payload": "result: 42", "context": {}}
{"event": "consumption", "action_id": "a2", "payload": "result: 42", "context": {}}
```

Rules: every `production` and `consumption` line's `action_id` must refer to
an `action_id` already introduced by an earlier `action` line in the same
file (raise a clear error if not, don't silently ignore it). `payload` is a
string, passed directly to `ArtifactIdentity.identify()` to resolve the
artifact id. A consumption whose payload doesn't exactly match any prior
production's payload will not resolve to the same artifact under
`ExactMatchArtifactIdentity`, and therefore won't produce a consumption edge
recorded against that artifact. This is expected behavior, faithfully
reflecting the exact-match limitation, not something to special-case around.
`context` is currently unused by `ExactMatchArtifactIdentity` but must be
accepted and passed through, since a future identity adapter will use it.

This schema is what a separate piece of work (writing the actual demonstration
scenarios) will target. Don't change field names or event types without
flagging it clearly, since that other work depends on this exact shape.

## Testing expectations

- Unit tests on `CouplingCalculator` with small, hand-built graphs, covering
  at minimum: zero coupling (every action only consumes its own or no
  artifacts), full coupling (every action consumes an unaccounted artifact
  from a different agent), the `TaskContext` carve-out (a `declared_inputs`
  set that should exclude a specific edge from counting), and a case where a
  consumption references an artifact id with no matching production (should
  be ignored, not raise).
- A unit test on `ExactMatchArtifactIdentity` demonstrating directly that two
  payloads differing by even one character produce different artifact ids,
  documenting the paraphrase limitation as a test, not just a docstring.
- Tests on `JsonlReplayAdapter` against a small fixture log file, checking it
  correctly drives all three `ObservationIngest` methods and raises clearly
  on a malformed reference to an undeclared `action_id`.
- No integration test against any live agent framework. Out of scope.

## Non-goals, repeated so nothing drifts during implementation

No intervention of any kind. No baseline learning, no anomaly model, no
shipped thresholds. No semantic or fuzzy artifact matching, exact match only.
No distributed or cross-host collection. No rendered visualization, only the
structured JSON export above. No demonstration scenario data, that's written
against this schema by someone else, not part of this build.

## Definition of done

`pyproject.toml` installs cleanly, `pytest` passes, `mypy` is clean or has
documented, justified exceptions, the repository layout above exists, every
port has at least one adapter implementing it, and a short `README.md`
explains how to install and run the tests (nothing more, no project narrative,
that's written elsewhere). At that point this is ready to be handed the two
demonstration event logs and run.

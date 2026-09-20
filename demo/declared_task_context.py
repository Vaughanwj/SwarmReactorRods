"""A scenario-specific TaskContext adapter for the demonstration.

This is deliberately not part of propagation_recorder's own adapters. The
library has no way to know what any real deployment's agents are assigned to
do — that mapping only exists in whoever wired the swarm up, and per the
return brief (decision 1 and the coupling formula, step 5) a wrong or missing
answer from TaskContext is exactly what turns a legitimate hand-off into a
false positive. So this mapping is supplied once, by hand, for this demo's two
scenarios, the same way a real deployment would supply its own.

Without something like this, NullTaskContext (which always returns None) marks
every cross-agent read as unaccounted, and a benign pipeline where agents
legitimately consume each other's output looks just as "coupled" as a steered
one. run_scenario.py runs both scenarios under both TaskContexts to show that
gap directly, rather than asserting it.
"""

from propagation_recorder.domain.models import AgentId, ArtifactId


class DeclaredTaskContext:
    """Looks up a fixed, hand-declared set of expected inputs per agent.

    `declared` maps an agent id to the set of artifact ids that agent's
    assigned task is expected to read from other agents. An agent absent from
    the mapping, or mapped to None, gets None back — "this system cannot say"
    — which the coupling formula treats as unaccounted, same as NullTaskContext
    would for that agent.
    """

    def __init__(self, declared: dict[AgentId, set[ArtifactId] | None]) -> None:
        self._declared = declared

    def declared_inputs(self, agent_id: AgentId) -> set[ArtifactId] | None:
        return self._declared.get(agent_id)

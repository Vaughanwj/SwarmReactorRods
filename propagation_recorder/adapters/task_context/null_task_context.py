from propagation_recorder.domain.models import AgentId, ArtifactId


class NullTaskContext:
    """Cannot say what any agent's job declares, so every cross-agent read counts."""

    def declared_inputs(self, agent_id: AgentId) -> set[ArtifactId] | None:
        return None

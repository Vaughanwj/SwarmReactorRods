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

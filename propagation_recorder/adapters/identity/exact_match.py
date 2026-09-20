import hashlib
from typing import Any

from propagation_recorder.domain.models import ArtifactId


class ExactMatchArtifactIdentity:
    """Identifies an artifact by the sha256 of its payload as UTF-8 bytes.

    Known, intentional limitation: this will not match paraphrased, summarized or
    partially quoted content. Two payloads differing by a single character get
    different ids, so an edge is only drawn for verbatim reuse. That is the v1
    design, not a bug to work around. `context` is accepted for a future identity
    adapter and ignored here.
    """

    def identify(self, payload: bytes | str, context: dict[str, Any]) -> ArtifactId:
        data = payload.encode("utf-8") if isinstance(payload, str) else payload
        return ArtifactId(hashlib.sha256(data).hexdigest())

from propagation_recorder.adapters.identity.exact_match import ExactMatchArtifactIdentity


def test_identical_payloads_match() -> None:
    ident = ExactMatchArtifactIdentity()
    assert ident.identify("result: 42", {}) == ident.identify(b"result: 42", {"x": 1})


def test_one_character_difference_gives_different_ids() -> None:
    """Documents the intentional paraphrase limitation."""
    ident = ExactMatchArtifactIdentity()
    assert ident.identify("result: 42", {}) != ident.identify("result: 43", {})
    assert ident.identify("result: 42", {}) != ident.identify("result: 42.", {})

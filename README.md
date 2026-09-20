# SwarmReactorRods

Measurement library that records which agent outputs each agent action consumed
and estimates coupling (k) over a time window. It measures only; it does not
intervene, block or classify anything.

## Install and test

Requires Python 3.12 or later.

```
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` elsewhere
pip install -e ".[dev]"
pytest
mypy
```

Design docs: `docs/build-brief.md` (spec, including the event log schema) and
`docs/architecture.md` (background).

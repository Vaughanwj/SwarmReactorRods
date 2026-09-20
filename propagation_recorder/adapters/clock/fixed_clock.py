from collections.abc import Iterable, Iterator
from datetime import datetime


class FixedClock:
    """Returns one fixed instant, or hands out a sequence of timestamps in order.

    With a sequence, calling now() past the end raises RuntimeError.
    """

    def __init__(self, timestamps: datetime | Iterable[datetime]) -> None:
        self._fixed: datetime | None = None
        self._it: Iterator[datetime] | None = None
        if isinstance(timestamps, datetime):
            self._fixed = timestamps
        else:
            self._it = iter(timestamps)

    def now(self) -> datetime:
        if self._fixed is not None:
            return self._fixed
        assert self._it is not None
        try:
            return next(self._it)
        except StopIteration:
            raise RuntimeError("FixedClock sequence exhausted") from None

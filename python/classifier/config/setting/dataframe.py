from __future__ import annotations

from typing import TYPE_CHECKING

from classifier.process.state import Cascade

if TYPE_CHECKING:
    from numpy.typing import DTypeLike


class Columns(Cascade):
    event: str = 'event'
    event_offset: str = 'event_offset'
    weight: str = 'weight'
    weight_normalized: str = 'weight_normalized'

    label_index: str = 'label_index'

    index_dtype: DTypeLike = 'uint8'

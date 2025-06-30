"""Simple heuristics to estimate pig length and weight from a bounding box."""
from typing import Tuple


def estimate_length_weight(box: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """Return approximate length and weight based on the bounding box.

    Parameters
    ----------
    box : Tuple[float, float, float, float]
        The bounding box coordinates in the form (x1, y1, x2, y2).

    Returns
    -------
    Tuple[float, float]
        Estimated length and weight in kilograms. The calculation is
        a rough guess; calibrate `SCALE_AREA_TO_WEIGHT` with real data
        for better accuracy.
    """
    x1, y1, x2, y2 = box
    length = x2 - x1
    area = (x2 - x1) * (y2 - y1)
    SCALE_AREA_TO_WEIGHT = 0.01
    weight = area * SCALE_AREA_TO_WEIGHT
    return length, weight

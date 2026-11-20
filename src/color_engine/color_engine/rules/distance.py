"""CIEDE2000 color difference."""

import numpy as np
from numpy.typing import NDArray
from skimage.color import deltaE_ciede2000


def ciede2000(lab_a: NDArray, lab_b: NDArray) -> NDArray[np.float64]:
    """Return the CIEDE2000 distance between two sets of CIELAB colors.

    Args:
        lab_a: Array with L, a, and b on the last axis.
        lab_b: Array with L, a, and b on the last axis. Its shape only needs to broadcast
            with ``lab_a``, so one color can be compared with many.

    Returns:
        float64 array of distances with the broadcast shape, without the last axis.
    """
    first, second = np.broadcast_arrays(
        np.asarray(lab_a, dtype=np.float64), np.asarray(lab_b, dtype=np.float64)
    )
    return np.asarray(deltaE_ciede2000(first, second))

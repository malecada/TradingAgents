"""Isotonic probability calibration on holdout folds.

Used per (model, horizon) to reduce miscalibration before the per-horizon
ensemble combiner (Task 25) takes weighted averages.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from sklearn.isotonic import IsotonicRegression


def calibrate_probabilities(model, X_holdout, y_holdout) -> Callable[[np.ndarray], np.ndarray]:
    """Fit isotonic regression on (model.predict_proba(X)[:, 1], y) and return
    a callable that maps raw probabilities → calibrated probabilities.

    The returned callable accepts a 1-D array of raw probabilities (the
    positive-class column of ``predict_proba``) and returns a 1-D array of
    calibrated probabilities of the same shape.
    """
    raw = model.predict_proba(X_holdout)[:, 1]
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    calibrator.fit(raw, y_holdout)
    return lambda p: calibrator.predict(p)

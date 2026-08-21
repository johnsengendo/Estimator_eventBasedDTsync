"""
Policies: when to spend a synchronisation.
=============================================================================

    run_periodic          fixed grid; blind to the data
    run_fixed_threshold   transmit whenever divergence exceeds a constant
    run_adaptive          threshold that adapts toward a target rate
    run_lyapunov          drift-plus-penalty against a virtual budget queue

References
----------
[1] M. J. Neely, "Stochastic Network Optimization with Application to
    Communication and Queueing Systems," Morgan & Claypool, 2010.
.
"""

import numpy as np

from estimators import ESTIMATORS


def run_periodic(pt, estimator_name, period):
    """Sync every `period` steps, blind to the data."""
    n = len(pt)
    dt = np.zeros(n)
    sync_flags = np.zeros(n, dtype=bool)
    est = ESTIMATORS[estimator_name](pt[0])
    dt[0], sync_flags[0] = pt[0], True

    for k in range(1, n):
        est.predict(k)
        sync = (k % period == 0)
        dt[k] = est.commit(k, sync, pt[k] if sync else None)
        sync_flags[k] = sync
    return dt, sync_flags


def run_fixed_threshold(pt, estimator_name, T):
    """Sync when the predicted divergence exceeds a fixed limit T."""
    n = len(pt)
    dt = np.zeros(n)
    sync_flags = np.zeros(n, dtype=bool)
    est = ESTIMATORS[estimator_name](pt[0])
    dt[0], sync_flags[0] = pt[0], True

    for k in range(1, n):
        pred = est.predict(k)
        e_k = abs(pt[k] - pred)
        sync = e_k > T
        dt[k] = est.commit(k, sync, pt[k] if sync else None)
        sync_flags[k] = sync
    return dt, sync_flags


def run_adaptive(pt, estimator_name, r_q, T0=0.05, eta=0.5, beta=0.98,
                 T_min=1e-4, T_max=0.5):
    """
    BUDGET-REFERENCED adaptive threshold.
    Tracks the recent sync rate with an EWMA and steers T toward the target:
      rate > r_q (syncing too much)   -> raise T (harder to sync)
      rate < r_q (syncing too little) -> lower T (easier to sync).
    """
    n = len(pt)
    dt = np.zeros(n)
    sync_flags = np.zeros(n, dtype=bool)
    est = ESTIMATORS[estimator_name](pt[0])
    dt[0], sync_flags[0] = pt[0], True

    T = T0
    rate = r_q                                     

    for k in range(1, n):
        pred = est.predict(k)
        e_k = abs(pt[k] - pred)
        sync = e_k > T
        dt[k] = est.commit(k, sync, pt[k] if sync else None)
        sync_flags[k] = sync

        rate = beta * rate + (1 - beta) * (1.0 if sync else 0.0)
        T = float(np.clip(T * (1 + eta * (rate - r_q)), T_min, T_max))  # steer T to target
    return dt, sync_flags


def run_lyapunov(pt, estimator_name, r_q, V, e_outage_thresh=None):
    """Drift-plus-penalty synchronisation against a virtual budget queue [1].

      sync  iff  e_k^2 > max(0, V * (Z_{k-1} + 1/2 - r_q))
      Z_k = max(0, Z_{k-1} + q_k - r_q)

    Z accumulates spend above the budget r_q; V weights accuracy against queue stability and is selected
    numerically (tuning.tune_lyapunov), the O(1/V) bound of [1] being asymptotic and assuming stationary arrivals.

    """
    n = len(pt)
    dt = np.zeros(n)
    sync_flags = np.zeros(n, dtype=bool)
    Z = np.zeros(n)
    est = ESTIMATORS[estimator_name](pt[0])
    dt[0], sync_flags[0] = pt[0], True

    for k in range(1, n):
        pred = est.predict(k)
        e_k = abs(pt[k] - pred)

        threshold = max(0.0, V * (Z[k - 1] + 0.5 - r_q))  # (2) budget-scaled moving bar
        sync = (e_k ** 2) > threshold

        if e_outage_thresh is not None and e_k > e_outage_thresh:  # (4) optional safety net
            sync = True

        dt[k] = est.commit(k, sync, pt[k] if sync else None)
        sync_flags[k] = sync
        Z[k] = max(Z[k - 1] + (1 if sync else 0) - r_q, 0.0)
    return dt, sync_flags, Z


# ===========================================================================
# 4. METRICS
# ===========================================================================


POLICIES = ["Periodic", "Adaptive", "Lyapunov"]   # Fixed-Threshold is frozen out

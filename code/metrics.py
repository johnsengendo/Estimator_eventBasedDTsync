"""
Metrics and synthetic traffic.
=============================================================================

    compute_metrics   score one run: overhead, mean/max divergence, outage
    generate_traffic  synthetic trace, used by the synthetic-data stages

Divergence is evaluated at every slot, including those with no transmission --
scoring only at sync instants would be misleading, since the twin is correct
there by construction.
"""

import numpy as np

def compute_metrics(pt, dt, sync_flags, outage_thresh=0.15, burn_in=0):
    """Overhead, mean divergence, outage rate, worst-case divergence.

    burn_in: number of initial slots to EXCLUDE from the metrics. Event-triggered
    policies with a virtual queue (Lyapunov) over-sync at the start while the queue
    fills; excluding a short warm-up window reports the true steady-state overhead
    and accuracy. burn_in=0 keeps the old behaviour (whole run)."""
    if burn_in > 0:
        pt = pt[burn_in:]
        dt = dt[burn_in:]
        sync_flags = sync_flags[burn_in:]
    e = np.abs(pt - dt)
    return {
        "overhead":          sync_flags.mean(),
        "mean_divergence":   e.mean(),
        "outage_prob":       (e > outage_thresh).mean(),
        "max_divergence":    e.max(),
        "divergence_series": e,
    }


# ===========================================================================
# 5. TUNING
# ===========================================================================


def generate_traffic(n_steps=2000, seed=0):
    """Synthetic PT trace: daily + weekly cycles, AR(1) noise, random bursts."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps)

    daily  = 0.5 + 0.4 * np.sin(2 * np.pi * t / 24 - np.pi / 2)
    weekly = 0.1  * np.sin(2 * np.pi * t / 168)

    noise = np.zeros(n_steps)
    phi, sigma_eta = 0.7, 0.03
    for k in range(1, n_steps):
        noise[k] = phi * noise[k - 1] + rng.normal(0, sigma_eta)

    signal = daily + weekly + noise

    n_bursts = max(1, n_steps // 300)
    burst_starts = rng.choice(n_steps - 10, size=n_bursts, replace=False)
    for s in burst_starts:
        dur = rng.integers(2, 6)
        amp = rng.uniform(0.3, 0.6)
        signal[s:s + dur] += amp

    signal = np.clip(signal, 0, None)
    return signal / signal.max()


# ===========================================================================
# 2. ESTIMATORS
# Shared interface, used identically by every policy:
#   predict(k)       -> "what will the DT display at step k WITHOUT a sync?"
#   commit(k, s, z)  -> advance internal state; if s (sync), absorb z=pt[k].
#                       Returns the value the DT actually displays at step k.
# ===========================================================================

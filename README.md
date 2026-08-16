# Estimator_eventBasedDTsync
# Event-Triggered Synchronisation for Cellular Digital Twins

**When is it worth running a model on the digital twin, and when is it better to
just hold the last value?**

A digital twin of a radio cell is only useful if it reflects the cell it
mirrors. Keeping it perfectly current would mean transmitting the measured state
every slot — exactly the bandwidth the network would rather spend on users. So
the twin is synchronised only occasionally, and in between it is on its own.

Two decisions have to be made, and they are usually conflated:

|  | Decision | Called here |
|---|---|---|
| **When** to spend a transmission | the triggering rule | the **policy** |
| **What** the twin shows in between | the state estimate | the **estimator** |

This work separates the two axes and measures them independently, which makes it
possible to ask a question a combined design cannot: *does a better estimator
still help once the trigger is already good?*

---

## System model

Time is slotted, one slot every 10 minutes.

- **Physical twin** — the true traffic load of a cell, `x_k`.
- **Digital twin** — a mirror `x̂_k` held remotely.
- **Synchronisation** — each slot the policy emits `s_k ∈ {0,1}`. If `s_k = 1`
  the true sample is transmitted and the estimator is corrected with it;
  otherwise nothing is sent and the twin displays the estimator's prediction.
- **Divergence** — `e_k = |x_k − x̂_k|`, evaluated at *every* slot, including
  those with no transmission. This is what a synchronisation scheme actually has
  to control.
- **Overhead** — `s̄ = (1/K) Σ_k s_k`, the fraction of slots transmitted.

### Problem

Given a communication budget `r_q`,

```
minimise    ē = (1/K) Σ_k e_k
subject to  s̄ ≤ r_q
```

The budget is a hard constraint, not a preference: in a deployment it is imposed
by the network, not chosen by the twin.

---

## The two design axes

**Policies — when to synchronise**

| Policy | Rule |
|---|---|
| **Periodic** | transmit every `⌈1/r_q⌉` slots; blind to the data, spends exactly the budget by construction |
| **Adaptive** | transmit when the predicted divergence crosses a threshold; reacts, but only after the error has grown |
| **Lyapunov** | keep a virtual queue `Z_{k+1} = max{0, Z_k + s_k − r_q}` and choose `s_k` by minimising a drift-plus-penalty term; enforces the budget over the horizon while steering each decision toward slots where divergence is accumulating |

**Estimators — what to display in between**

| Estimator | Idea | Model-based |
|---|---|---|
| **Hold** | freeze the last received value | no |
| **Linear** | extrapolate the last observed slope | no |
| **OscKalman** | Kalman filter carrying a daily harmonic, so the cycle keeps turning while the twin is blind | yes |
| **GapAdapt** | a multi-harmonic Kalman filter blended toward the last received value, weighted by how long the twin has been blind | yes |

For the cycle-aware filters the **period is supplied** (one day); the
**amplitude and phase are learned** from the synchronisations received.

---

## Characterising a cell

How much structure a cell contains turns out to determine everything. For a
trace of whole days at `P` slots per day, let `x̄_p` be the mean value at phase
`p` of the day and `ε_k = x_k − x̄_{k mod P}` the residual. Then

```
ρ = 1 − Var(ε) / Var(x)
```

is the fraction of variance explained by an average-day profile: `ρ → 1` for a
clean daily rhythm, `ρ → 0` for transient-dominated traffic. It depends on the
trace alone, so it can serve as a *deployment criterion* rather than a post-hoc
explanation.

Evaluation uses one week of the
[Telecom Italia Milan](https://doi.org/10.7910/DVN/EGZHFV) open dataset, on
three cells spanning the range — `ρ = 0.91`, `0.56` and `0.07` — across target
budgets from 2% to 10%. Estimator parameters are tuned once on a separate
held-out cell and then frozen, so all results are out-of-sample.

---

## What comes out of it

1. **Model-based estimation is not universally better.** Its benefit is
   predicted by `ρ`, computable in advance, and by how scarce the budget is —
   an operating envelope rather than a blanket recommendation. On the structured
   cells the model cuts divergence by 12–34% against holding the last value; on
   the unstructured cell it does not help at all.

2. **A budget-capped Lyapunov trigger meets a hard communication constraint
   without paying for it in accuracy.** It stayed at or below target in every
   configuration tested while also reaching the lowest divergence, so accuracy
   and communication cost were not traded off against one another.

3. **Policy and estimator are partial substitutes.** A trigger that fires when
   divergence is growing already removes much of the staleness an estimator
   exists to compensate for, so the marginal value of a better estimator shrinks
   as the trigger improves.

4. **Model mismatch is worse than no model.** Extrapolating a slope is the worst
   choice in nearly every configuration, and a richer harmonic model fits noise
   rather than signal on traffic without a rhythm.

---

## Contents

```
figures/   result figures
data/      the numerical values behind each figure (CSV) + short notes
docs/      extended explanation of the estimators and the tuning procedure
```

The implementation is not included here yet. The Milan dataset is not
redistributed — it is public at the link above.

## License

Figures, data and documentation under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

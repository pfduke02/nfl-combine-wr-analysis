"""Does a spiky combine profile predict WR draft over/under-performance?

For each drafted WR (2006-2018 combines), take the six workout z-scores
(WR-relative, higher = better) and compute their per-player SD — high SD means
an uneven profile (e.g. elite forty, weak agility), low SD a balanced one.
Success = resid from wr_drafted_with_expectation.csv (career games started
minus the fitted expectation for that draft slot).

Tests: resid ~ sd_z, resid ~ weight, and both jointly (with mean_z as a
control so sd_z isn't just proxying overall athleticism).

Outputs: wr_sd_vs_success.png, printed correlations/regression.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from wr_workout_z import WORKOUTS, height_to_inches, zscore_within_wr

MIN_DRILLS = 4  # SD over fewer drills is too noisy


def build_table() -> pd.DataFrame:
    wr = pd.read_csv("wr_combine_success_2006_2018.csv")
    wr["ht_in"] = height_to_inches(wr["ht"])
    z = zscore_within_wr(wr)[WORKOUTS]

    wr["n_drills"] = z.notna().sum(axis=1)
    wr["mean_z"] = z.mean(axis=1)
    wr["sd_z"] = z.std(axis=1, ddof=1)

    # join on player+season: pfr_id is NaN for players who never made the
    # NFL, and pandas matches NaN keys to NaN, cross-joining those rows
    drafted = pd.read_csv("wr_drafted_with_expectation.csv")
    d = wr.merge(drafted[["player_name", "season", "expected", "resid"]],
                 on=["player_name", "season"])
    return d[d["n_drills"] >= MIN_DRILLS].copy()


def report(x, y, label):
    r, p = stats.pearsonr(x, y)
    rho, ps = stats.spearmanr(x, y)
    print(f"{label:>28}: pearson r={r:+.3f} (p={p:.3f}), "
          f"spearman rho={rho:+.3f} (p={ps:.3f})")
    return r, p


def main():
    d = build_table()
    print(f"drafted WRs with >= {MIN_DRILLS} drills: {len(d)}")
    print(f"sd_z: mean {d['sd_z'].mean():.2f}, range "
          f"{d['sd_z'].min():.2f}-{d['sd_z'].max():.2f}\n")

    r_sd, p_sd = report(d["sd_z"], d["resid"], "SD of z (spikiness)")
    r_wt, p_wt = report(d["wt"], d["resid"], "weight (lbs)")
    report(d["mean_z"], d["resid"], "mean z (overall athleticism)")

    # joint OLS: resid ~ sd_z + weight + mean_z
    X = np.column_stack([np.ones(len(d)), d["sd_z"], d["wt"], d["mean_z"]])
    beta, *_ = np.linalg.lstsq(X, d["resid"], rcond=None)
    resid_hat = X @ beta
    ss_res = np.sum((d["resid"] - resid_hat) ** 2)
    ss_tot = np.sum((d["resid"] - d["resid"].mean()) ** 2)
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * ss_res / (len(d) - X.shape[1]))
    t = beta / se
    pvals = 2 * stats.t.sf(np.abs(t), len(d) - X.shape[1])
    print("\njoint OLS: resid ~ sd_z + weight + mean_z "
          f"(R^2={1 - ss_res / ss_tot:.3f})")
    for name, b, s, pv in zip(["intercept", "sd_z", "weight", "mean_z"],
                              beta, se, pvals):
        print(f"  {name:>9}: beta={b:+8.2f}  se={s:6.2f}  p={pv:.3f}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    for ax, col, xlabel, (r, p) in [
        (axes[0], "sd_z", "SD of workout z-scores (profile spikiness)", (r_sd, p_sd)),
        (axes[1], "wt", "weight (lbs)", (r_wt, p_wt)),
    ]:
        ax.scatter(d[col], d["resid"], s=20, alpha=0.4, color="steelblue")
        m, b0 = np.polyfit(d[col], d["resid"], 1)
        xs = np.linspace(d[col].min(), d[col].max(), 50)
        ax.plot(xs, m * xs + b0, color="crimson", lw=2,
                label=f"r={r:+.2f}, p={p:.3f}")
        ax.axhline(0, color="gray", lw=0.8, ls=":")
        ax.set_xlabel(xlabel)
        ax.legend()
    axes[0].set_ylabel("career starts minus draft-slot expectation")
    fig.suptitle("WR success vs. combine profile spikiness and weight "
                 "(drafted, 2006-2018 classes)")
    fig.savefig("wr_sd_vs_success.png", dpi=120, bbox_inches="tight")


if __name__ == "__main__":
    main()

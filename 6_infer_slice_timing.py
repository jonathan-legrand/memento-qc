"""
At the end of this notebook, informed by many
pretty plots, we come up with a rule to determine
which scans have been acquired in an interleaved
setting and need correction.
"""
# %%
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

rsfmris = pd.read_csv(
        "output/slice_timing/lags.csv",
        index_col=0
    )
# %% 
# Estimates of lag are quite noisy, as they
# can be disturbed by head motion.
# Not reliable if not many scans
fig, axes = plt.subplots(1, 2, figsize=(10, 8), sharey=True)

centre_counts = rsfmris.groupby(by="centre")["centre"].count().sort_values(ascending=False)

sns.violinplot(
    rsfmris[abs(rsfmris.lag) < 1.5],
    x="lag",
    y="centre",
    hue="centre",
    order=centre_counts.index,
    hue_order=centre_counts.index,
    ax=axes[0]
)
axes[0].set_xlabel("lag (TR)")
axes[0].set_title("Odd-Even Slices Lag")

sns.barplot(
    y=centre_counts.index,
    x=centre_counts.values,
    hue=centre_counts.index,
    ax=axes[1]
)
axes[1].set_xlabel("#scans")
axes[1].set_title("Number of Scans")
fig.suptitle("Slice Timing Study", y=0.93)
plt.show()
# %% It's not enough to compute one lag per centre,
# most probably it also changes with the machines.
# We load the cati_monito file, which contains 
# information on which machine was used for each
# scan

monito = pd.read_csv("/georges/memento/BIDS/cati_monito_2.txt", sep="\t")
monito["short_id"] = monito.loc[:, "NUM_ID"].map(lambda x: x[4:])

mm = monito.melt(
    id_vars="short_id",
    value_vars=["Machine_M0", "Machine_M24", "Machine_M48"],
    value_name="machine"
)

mm["session"] = mm["variable"].map(
    {
        "Machine_M0": "M000",
        "Machine_M24": "M024",
        "Machine_M48": "M048"
    }
)
merged = pd.merge(
    left=rsfmris,
    right=mm,
    how="inner",
    left_on=["session", "short_id"],
    right_on=["session", "short_id"]
)
# %% Violin plot for machines instead of centres
machine_count = merged.groupby(by="machine")["machine"].count().sort_values(ascending=False)

g = sns.catplot(
    merged[abs(merged.lag) < 1.5],
    kind="violin", 
    x="lag",
    y='machine',
    hue="machine",
    order=machine_count.index,
    hue_order=machine_count.index,
    height=10,
    inner=None,
    fill=None,
    bw_adjust=.20,
    legend=False
)
sns.stripplot(
    merged[abs(merged.lag) < 1.5],
    x="lag",
    y="machine",
    color="k",
    size=3,
    ax=g.ax
)

g.ax.set_xlabel("lag (TR)")
g.ax.set_title("Odd-Even Slices Lag")
plt.show()

# %% That's the plot we need to take a decision
merged["centre / machine"] = merged["centre"] + " - " + merged["machine"]

sns.catplot(
    merged[abs(merged.lag) < 1.5].sort_values(by="centre / machine"),
    kind="strip",
    x="lag",
    y="centre / machine",
    hue="centre",
    legend=None,
    height=14,
    aspect=0.8
)
plt.show()
# %%
# Reliable estimates
res = merged[abs(merged.lag) < 1.5].groupby("centre / machine")["lag"].median()
# Keep the ones which seem to have an offset
res_ = res[res.values.__abs__() > 0.1]
print(res_)
# %%
from scipy.stats import ttest_1samp, bootstrap
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages


def is_lag_significant(
    lag_samples:np.ndarray
):
    
    res = bootstrap(
        lag_samples.reshape(1, -1),
        np.median,
        n_resamples=len(lag_samples) * 10
    )
    _, p = ttest_1samp(res.bootstrap_distribution, 0.)
    return p


tests = []
merged = merged[abs(merged.lag) < 3 / 2]

with PdfPages("output/slice_timing/significant_lags.pdf") as pdf:
    for centre_machine in merged["centre / machine"].unique():
        lags = merged[merged["centre / machine"] == centre_machine]["lag"].to_numpy()
        if len(lags) > 3:
            res = is_lag_significant(lags)
            print(f"{centre_machine}, significant lag is {res}")
            tests.append((centre_machine, res))
            if res < 0.05:
                sns.swarmplot(x=lags, color="red")
                sns.boxplot(x=lags, fill=None, color="blue")
                plt.title(f"{centre_machine}, p={res:.2f}")
                plt.xlabel("Time (TR)")
                pdf.savefig()
                plt.close()

tests = pd.DataFrame(tests, columns=["centre / machine", "is_lag_significant"])
tests[tests.is_lag_significant < 0.01].sort_values(by="is_lag_significant")
# %%

def decision_rule(row):
    criteria = [
        ((row.machine == "GE MR Discovery 3T") & (row.centre != "RQS")),
        ((row.machine == "GE Signa 3T") & (row.centre != "VQS")),
        (row.machine == "Siemens Symphonytim Avanto 1.5T"),
    ]
    return np.logical_or.reduce(criteria)

merged["interleaved"] = merged.apply(decision_rule, axis=1)
# %%
sns.catplot(
    merged[(abs(merged.lag) < 1.5) & merged.interleaved].sort_values(by="centre / machine"),
    kind="violin",
    x="lag",
    y="centre / machine",
    hue="centre",
    fill=None,
    inner="point",
    legend=None,
    bw_adjust=0.5,
    height=14,
    aspect=0.8
)


plt.show()

merged[merged.interleaved].to_csv("output/slice_timing/interleaved.csv")
# %%

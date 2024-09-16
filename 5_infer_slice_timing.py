"""
Slice timing information is missing from
the files we received from the CATI.
Let's guess slice timing by
ourselves, by analysing the lag between
odd and even slices.
Most probably, the slice timing is different between centres,
and between machines, knowing that some centres change their
machines during the course of the study.
At the end of this notebook, informed by many
pretty plots, we come up with a rule to determine
which scans have been acquired in an interleaved
setting and need correction.
"""
# %%
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy import signal

from pathlib import Path
from bids import BIDSLayout
import bids

from utils.visualisation import make_and_show_middle_slices
from slice_timing.correlation import make_slice_corr_map, odd_slices_lag, rsfmri_lag
from slice_timing.plotting import show_slice_timing
from mappings.centres import fetch_centre
from mappings.slice_timing import multiband_slice_timing

INPUT_PATH = Path("/georges/memento/BIDS")
SHOW_SLICES = False
FROM_FILE = False

# %% Load data

participants = pd.read_csv(INPUT_PATH / "participants.tsv", sep="\t")

try:
    # Yes it has been validated don't worry
    layout = BIDSLayout(database_path="pybids")
except TypeError: # This is the stupidest thing to raise
    layout = BIDSLayout(
        INPUT_PATH, 
        validate=False,
        index_metadata=False
    )

df = layout.to_df()
rsfmris = df[(df.suffix == "bold") & (df.extension == ".nii.gz") & (df.acquisition != "rejected")]

participants["short_id"] = participants.participant_id.map(lambda x: x[4:])

rsfmris = pd.merge(
    left=rsfmris,
    right=participants,
    how="inner",
    left_on="subject",
    right_on="short_id"
)


# %%
for centre in rsfmris.centre.unique():
    sample_mask = (rsfmris.centre == centre)
    sample_mask = sample_mask

    sample = rsfmris[sample_mask].sample(n=1)
    sample_path = sample.path.values[0]

    # Why such a backward logic
    rsfmri = bids.layout.models.BIDSFile(sample_path)
    rsfmri.centre = sample.centre.values[0]
    img = nib.load(rsfmri.path).get_fdata()

    if SHOW_SLICES:
        make_and_show_middle_slices(img.mean(axis=3))
        plt.suptitle(rsfmri.filename)
        plt.show()

    mat, corr_map = make_slice_corr_map(img)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(f"{rsfmri.filename}, centre {rsfmri.centre}")
    
    axes[0].plot(mat.T)
    axes[0].set_xlabel("TR")
    axes[0].set_title(f"Standardized slice signals")

    sns.heatmap(corr_map, cmap="magma", ax=axes[1])
    axes[1].set_title(
        "slice signals correlation"
    )
    axes[1].set_xlabel("Slice index")
    plt.show()

    plt.plot(mat.T)
    plt.xlabel("TR")
    plt.title(f"Slice signals, {rsfmri.filename}, centre {rsfmri.centre}")
    plt.show()
    break
    
odd_slices_lag(mat)


# %% Slice timing visualisations because my brain
# is slow
show_slice_timing(multiband_slice_timing)
plt.title("Multiband acquisition")
plt.show()

show_slice_timing([0, 0.85/2] * 33)
plt.title("Interleaved acquisition")
plt.show()

show_slice_timing([0.85/2] * 66)
plt.title("Corrected by interpolation")
plt.show()

# %% Get per centre lag distribution

if FROM_FILE:
    rsfmris = pd.read_csv(
        "output/slice_timing/lags.csv",
        index_col=0
    )
else:
    rsfmris["lag"] = rsfmris.loc[:, "path"].map(rsfmri_lag) 

# %%
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


# %%

monito = pd.read_csv("/bigdata/jlegrand/data/Memento/cati_monito_2.txt", sep="\t")
monito["short_id"] = monito.loc[:, "NUM_ID"].map(lambda x: x[4:])
#monito["Machine_M48"] = "Unspecified"

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


# %% Centre repartition per machine
machine = 'Unspecified'
msk = (merged.machine == machine) & (merged.lag.__abs__() < 1.5)
c = merged[msk].groupby("centre")["centre"].count().sort_values(ascending=False)

sns.violinplot(
    merged[msk],
    x="lag",
    hue="centre",
    hue_order=c.index,
    fill=None
)
#sns.swarmplot(
#    merged[msk],
#    x="lag",
#    hue="centre",
#    hue_order=c.index
#)
plt.title(machine)
plt.show()
merged[msk].lag.median()
sns.barplot(y=c.index, x=c.values)
plt.show()
# %%

mc = merged.melt(
    id_vars=["centre", "lag", "session", "machine"]
)

# %%
sns.catplot(
    merged[abs(merged.lag) < 1.5],
    x="lag",
    y="centre",
    hue="machine",
    kind="strip",
    row="session",
    size=4,
    height=5
)
plt.show()

# %%
merged["centre / machine"] = merged["centre"] + " - " + merged["machine"]

sns.catplot(
    merged[abs(merged.lag) < 1.5].sort_values(by="centre / machine"),
    kind="box",
    x="lag",
    y="centre / machine",
    hue="centre",
    fill=None,
    #inner="point",
    legend=None,
    #bw_adjust=0.5,
    height=14,
    aspect=0.8
)
plt.show()
# %%

res = merged[abs(merged.lag) < 1.5].groupby("centre / machine")["lag"].median()
res_ = res[res.values.__abs__() > 0.1]
print(res_)

# %%
from scipy.stats import ttest_1samp, shapiro, mannwhitneyu, bootstrap
import warnings
one_centre = merged[
    merged['centre / machine'] == "RQG - GE MR Discovery 3T"
    ]["lag"].to_numpy() 

def is_lag_significant(
    lag_samples:np.ndarray
):
    
    res = bootstrap(
        lag_samples.reshape(1, -1),
        np.median,
        n_resamples=len(lag_samples) * 10
    )
    # Normality checks. You don't want to see that.
    #plt.hist(res.bootstrap_distribution)
    #plt.title("Boostrapped medians")
    #print(f"p_shapiro = {shapiro(res.bootstrap_distribution)[1]:.2f}")
    # Rise and catch degenerate distributions
    _, p = ttest_1samp(res.bootstrap_distribution, 0.)
    return p

print(f"test lag p = {is_lag_significant(one_centre):.2f}")


# %%

from matplotlib.backends.backend_pdf import PdfPages

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
                #pdf.savefig()
                #plt.close()
                plt.show()


tests = pd.DataFrame(tests, columns=["centre / machine", "is_lag_significant"])
tests[tests.is_lag_significant < 0.01].sort_values(by="is_lag_significant")

# %%

def decision_rule(row):
    criteria = [
        ((row.machine == "GE MR Discovery 3T") & (row.centre != "RQS")),
        ((row.machine == "GE Signa 3T") & (row.centre != "VQS")),
        (row.machine == "Siemens Symphonytim Avanto 1.5T"),
        ((row.machine == "Unspecified") & (row.centre == "JGX"))
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
# %%

#merged[merged.interleaved].to_csv("output/slice_timing/interleaved.csv")
# %%

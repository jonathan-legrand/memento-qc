"""
Slice timing information is missing from
the files we received from the CATI.
Let's guess slice timing by
ourselves, by analysing the lag between
odd and even slices.
Most probably, the slice timing is different between centres,
and between machines, knowing that some centres change their
machines during the course of the study.
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

# %% Get per centre lag distribution.
# This is EXTREMLY slow

rsfmris["lag"] = rsfmris.loc[:, "path"].map(rsfmri_lag) 
rsfmris.to_csv("output/slice_timing/lags.csv")


# %%

# %%
import nibabel as nib
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from slice_timing.estimation import make_st
from bids_handlers.sidecar import Sidecar
from slice_timing.plotting import show_slice_timing

rsfmris = pd.read_csv("output/slice_timing/interleaved.csv", index_col=0)
interleaved = rsfmris[rsfmris.interleaved]

def make_sidecar_path(path):
    return path.split(".")[0] + ".json"


# %%
slice_timings = interleaved["path"].map(make_st)
sidecar_paths = interleaved["path"].map(make_sidecar_path)

# Display sample st
sample = slice_timings.sample(n=1).to_list()[0]
show_slice_timing(sample, TR=sample[1] * 2)

sidecars = sidecar_paths.map(Sidecar.from_path)

# %%
# Be careful, this writes in the actual BIDS repository
for st, sidecar in zip(slice_timings, sidecars):
    sidecar["SliceTiming"] = st
    sidecar.write()


# %%

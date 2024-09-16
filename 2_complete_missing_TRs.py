"""
Fill the missing TR information directly inside the BIDS
directory. This should have been done during the transfer
since it's a BIDS compliance matter but whatever.
This script requires an inferred_TRs.csv file containing
the subjects with no TR and their inferred values, which
can be generated from checkdims.py
"""

# %%
import nibabel as nib
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from bids import BIDSLayout
import json

from mappings.sidecar import bold_sidecar


# %%
TR_PATH = Path("output/inferred_TR.csv")
#INPUT_PATH = Path("/georges/memento/BIDS")
INPUT_PATH = Path("/scratch/memento_sample_bids")
layout = BIDSLayout(INPUT_PATH)

TRs = pd.read_csv(TR_PATH, index_col=0, dtype={"subject_id": str})
# %%

for _, row in TRs.iterrows():
    print(row.subject_id)
    try:
        sidecar, rsfmri = layout.get(
            subject=row.subject_id,
            session=row.month,
            suffix="bold"
        )
    except ValueError:
        print(
            f"sub-{row.subject_id}_ses-{row.month} not in layout, skipping"
        )
    sidecar_dct = eval(sidecar.get_json())

    old_img = nib.load(rsfmri.path)
    updated_img = old_img
    zooms = updated_img.header.get_zooms()[:3] + (row.inferred_TR,)
    updated_img.header.set_zooms(zooms)

    sidecar_dct["RepetitionTime"] = row.inferred_TR
    with open(sidecar.path, "w") as f:
        json.dump(sidecar_dct, f)
    
    nib.save(updated_img, rsfmri.path) # Be careful, this overwrites stuff

# %%

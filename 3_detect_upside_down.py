"""
Detect upside down brains.
We're using the distance in the scanner space between
reference and bold FOV centers to detect bad q matrices.
"""
# %%
from pathlib import Path
import warnings
import nibabel as nib
import numpy.linalg as npl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import bids
from bids import BIDSLayout

from utils.visualisation import make_and_show_middle_slices

from qc.scanner_space import distance_between_FOVs

INPUT_PATH = Path("/scratch/memento_sample_bids")
try:
    layout = BIDSLayout.load("pybids_samples")
except TypeError:
    layout = BIDSLayout(
        INPUT_PATH, 
        validate=False,
        index_metadata=False,
        database_path="pybids_samples"
    )
# %% Show a known example
SUBJECT = "0142"
boldf = layout.get(subject=SUBJECT, session="M000", suffix="bold", extension=".nii.gz")[0]
t1wf = layout.get(subject=SUBJECT, session="M000", suffix="T1w", extension=".nii.gz")[0]

bold_img = nib.load(boldf.path)
t1w_img = nib.load(t1wf.path)
bold_arr = bold_img.get_fdata()
t1w_arr = t1w_img.get_fdata()

make_and_show_middle_slices(bold_arr)
plt.show()

make_and_show_middle_slices(t1w_arr.transpose(2, 0, 1))
plt.show()
# %%

qa = []
rsfmris = layout.get(suffix="bold", extension="nii.gz")
for i, rsfmri in enumerate(rsfmris):
    subject = rsfmri.entities["subject"]
    session = rsfmri.entities["session"]

    try:
        reference = layout.get(
            subject=subject,
            session=session,
            suffix="T1w",
            extension=".nii.gz"
        )[0]
    except IndexError:
        warnings.warn(f"{rsfmri.path} has no T1w reference image, skipping")
        continue

    reference_img = nib.load(reference.path)
    rsfmri_img = nib.load(rsfmri.path)
    
    subject_dict = {
        **{"distance_FOVs" : distance_between_FOVs(reference_img, rsfmri_img)},
        **rsfmri.entities
    }
    qa.append(subject_dict)

df = pd.DataFrame(qa)

# %%
sns.boxplot(df, x="distance_FOVs")
plt.xlabel("distance between FOVs (mm)")
plt.show()

# %% Export subjects with high distances
msk = df.distance_FOVs > 50
from matplotlib.backends.backend_pdf import PdfPages

with PdfPages("output/QC/descending.pdf") as pdf:
    for i, row in df[msk].sort_values(by="distance_FOVs", ascending=False).iterrows():
        # Should have added path in df but whatever
        rsfmri = layout.get(
           subject=row.subject,
           session=row.session,
           suffix="bold",
           extension=".nii.gz"
        )[0]
        img = nib.load(rsfmri.path)
        make_and_show_middle_slices(img.get_fdata())
        plt.suptitle(f"{rsfmri.filename}\nd={row.distance_FOVs:.2f}mm")
        pdf.savefig()
        plt.close()

# %%

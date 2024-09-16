"""
Find out if memento rsfmri sequences have the proper
number of sequences and consistent repetition times.
"""

# %%
import nibabel as nib
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import numpy as np
import seaborn as sns

from mappings.fnames import BOLD_FNAMES, ALL_BOLD_FNAMES, ALL_T1_FNAMES
from utils.file_matcher import recursive_file_matcher
from utils.visualisation import make_and_show_middle_slices
from utils.sequence_report import sequence_report, sequence_report_with_units
from utils.memento_structure import extract_info

MEMENTO_PATH = Path("/georges/memento/IRM")

# %% Display examples of slices invalid sequences

invalid_seq_path = MEMENTO_PATH / 'M000_M024/DOT/SUBJ0158/M048/mri_rsfmri_rsfmri_nifti.nii.gz'
invalid_seq = nib.load(invalid_seq_path)
invalid_vol = invalid_seq.get_fdata()

# Extract images along the last dimension
# (which should be time for a normal sequence)
# of the bad sequence and export to pdf
centre, month, subject_id = extract_info(invalid_seq_path)
with PdfPages(f"output/QC/sub-{subject_id}_ses-{month}.pdf") as pdf:
    for k in range(0, invalid_vol.shape[-1], 1000):
        plt.imshow(invalid_vol[:, :, k])
        plt.title(f"k = {k}")
        pdf.savefig()
        plt.close()

# %% Report information on all the files which match authorised
# BOLD file names. This can take some time.

bold_nifti_paths = recursive_file_matcher(MEMENTO_PATH, ALL_BOLD_FNAMES)

reports = []
for bold_nifti_path in bold_nifti_paths:
    print(bold_nifti_path)
    reports.append(sequence_report_with_units(bold_nifti_path))
    

df = pd.DataFrame(
    reports,
    columns=[
        "subject_id",
        "centre",
        "month",
        "is_4D",
        "Tr (s)",
        "nifti_path",
        "x",
        "y",
        "z",
        "t",
        "vox_units",
        "time_units"
    ]
).drop_duplicates(subset=["subject_id", "centre", "month"])
# %% Plot some interesting results

counts = df.groupby("centre").size().sort_values(ascending=False)
sns.barplot(y=counts.index, x=counts.values)
plt.title("Scans per centre")
plt.show()


sns.stripplot(df, x="Tr (s)")
plt.title("Répartition des Tr")
plt.show()


# %%

df["is_not_4D"] = ~df["is_4D"]
bad_seq_counts = df.groupby("centre").is_not_4D.sum()
msk = (bad_seq_counts != 0)
sns.barplot(y=bad_seq_counts[msk].index, x=bad_seq_counts[msk].values)
plt.title("Number of non 4D files per centre")
plt.show()


# %%
sns.boxplot(df, x="Tr (s)", y="centre")
plt.title("Tr repartition per centre")
plt.show()

# %% Number of rsfmri scans. Be careful, there are many duplicates.
g = sns.countplot(df, x="month", order=["M000", "M024", "M048"])
abs_values = df['month'].value_counts(ascending=False).values

g.bar_label(container=g.containers[0], labels=abs_values)
plt.title("Number of scans per timestep")
plt.show()


# %%
df["fname"] = df.nifti_path.apply(lambda path: path.stem)
sns.countplot(df, y="fname")
plt.title("Repartition of file names")
plt.show()
# %% Spatial dimensions
s_melt = df[df["is_4D"]].melt(value_vars=["x", "y", "z"])
sns.boxplot(s_melt, x="value", y="variable")
plt.show()

# %%
spatial_outliers_msk = np.logical_or(
    df.x != 64,
    df.y != 64,
    (df.z < 30) & (df.z > 50),
)
spatial_outliers = df[spatial_outliers_msk]
spatial_outliers

# %%
temporal_outliers = df[(df.t < 120) & (df.is_4D)].sort_values(by="t")
sns.countplot(temporal_outliers, y="centre")
plt.title("Temporal outliers per centre (t < 120)")
plt.xticks(range(4))
plt.show()
# %% Infer TR when it is missing

def infer_TR(row, frame):
    """
    For a given row, returns the median TR from the same centre and
    with the same number of slices.
    """
    msk = (frame.centre == row.centre) & (frame.z == row.z) & (frame["Tr (s)"] != 0)
    return frame.loc[msk, "Tr (s)"].median()

missing_TRs = df[df["Tr (s)"] == 0].copy()
missing_TRs.loc[:, "inferred_TR"] = missing_TRs.apply(infer_TR, axis=1, args=[df])
missing_TRs.to_csv("output/inferred_TR.csv")

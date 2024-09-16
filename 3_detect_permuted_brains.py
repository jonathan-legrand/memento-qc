"""
Some rsfmri in memento show permuted voxels which should be detected
early because they make mriqc crash
"""
# %%
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import seaborn as sns
from scipy.signal import convolve2d, periodogram

from pathlib import Path
import random
from bids import BIDSLayout

from qc.sum_of_gradients import middle_gradients_qa, sobel_x
from utils.visualisation import make_and_show_middle_slices
from transformations.permutation import destripe_img, convert_outliers

INPUT_PATH = Path("/scratch/memento_sample_bids")
random.seed(1234)
try:
    layout = BIDSLayout.load("pybids_samples")
except TypeError:
    layout = BIDSLayout(
        INPUT_PATH, 
        validate=False,
        index_metadata=False,
        database_path="pybids_samples"
    )
# %%

bad_rsfmri = layout.get(subject="0071", suffix="bold", extension="nii.gz")[0]

rsfmris = layout.get(suffix="bold", extension="nii.gz")
control_rsfmri = random.choice(rsfmris)


bad_img = nib.load(bad_rsfmri.path).get_fdata()
bhdr = nib.load(bad_rsfmri.path).header
control_img = nib.load(control_rsfmri.path).get_fdata()

# %% Show gradient magnitude examples

make_and_show_middle_slices(bad_img.mean(axis=3))
plt.suptitle(f"sub-{bad_rsfmri.entities['subject']}, mean over time")
plt.show()

make_and_show_middle_slices(control_img.mean(axis=3))
plt.suptitle(f"sub-{control_rsfmri.entities['subject']}, mean over time")
plt.show()

imb = bad_img[30, :, :, :].mean(axis=2)
imc = control_img[30, :, :, :].mean(axis=2)

# Gradients magnitude along x axis should be low
# for permuted brains
grad_bad = abs(convolve2d(imb, sobel_x, boundary='symm', mode='same'))
grad_control = abs(convolve2d(imc, sobel_x, boundary='symm', mode='same'))

fig, ax = plt.subplots(2, 2)

ax[0,0].imshow(imc.T, cmap="gray", origin="lower")
ax[0,0].set_title(f"sub-{control_rsfmri.entities['subject']}, mean over time")

ax[0,1].imshow(imb.T, cmap="gray", origin="lower")
ax[0,1].set_title(f"sub-{bad_rsfmri.entities['subject']}, mean over time")


ax[1, 0].imshow(grad_control.T, cmap="gray", origin="lower")
ax[1, 0].set_title(
    f"Gradient magnitude along x axis"
)

ax[1,1].imshow(grad_bad.T, cmap="gray", origin="lower")
ax[1,1].set_title(
    f"Gradient magnitude along x axis"
)

fig.tight_layout()
plt.show()

st = np.vstack(
    (
        grad_control.ravel() / imc.std(),
        grad_bad.ravel() / imb.std()
    )
).T
plt.hist(st, bins=40, label=("Control", "Permuted image"))
plt.legend()
plt.title("Gradient magnitude over x, standardized repartition")
plt.xlabel("Magnitude")
plt.ylabel("Count")
plt.show()
        
# %% Detect outliers

global_qa = []
rsfmris = layout.get(suffix="bold", extension="nii.gz")
for i, rsfmri in enumerate(rsfmris):
    print(f"{rsfmri.filename} {i + 1}/{len(rsfmris)}")
    image = nib.load(rsfmri.path).get_fdata()
    qa = dict(middle_gradients_qa(image))
    subject_dict = {**qa, **rsfmri.entities}
    global_qa.append(subject_dict)

df = pd.DataFrame(global_qa)


# %%
m = df.melt(
    id_vars=["subject", "session"],
    value_vars=["sagittal", "coronal", "transverse"],
    var_name="plane",
    value_name="Absolute partial derivative"
)
sns.histplot(m, x="Absolute partial derivative", hue="plane")
plt.show()
sns.boxplot(m, x="Absolute partial derivative", hue="plane")
plt.show()
# %% Match outliers with centers

participants = pd.read_csv(INPUT_PATH / 'participants.tsv', sep="\t")
participants["subject"] = participants.participant_id.map(lambda x: x[4:])

merged = pd.merge(
    participants,
    df,
    how="inner",
    left_on=["subject"],
    right_on=["subject"]
)

sns.countplot(merged[merged.sagittal < 1000], x="centre")
plt.title("Outliers per centre")
plt.show()
merged[merged.sagittal < 1000].to_csv("output/permuted_brains.csv")

# %% There is a saving/loading point to avoid computing
# the gradients each time
# This part of the code fixes the images which
# have been flagged as outliers and stores them
# in a temporary directory
import os
outliers = pd.read_csv("output/permuted_brains.csv", index_col=0)

os.makedirs("/tmp/permutation_experiment", exist_ok=True)
convert_outliers(outliers, layout, overwrite_bids=False)

# %% 
    
def generate_reports(outliers):
    for _, s in outliers.iterrows():
        bids_name = f"{s.participant_id}_ses-{s.session}_task-rest_bold.nii.gz"
        print(bids_name)
        with PdfPages(f"output/QC/{bids_name}.pdf") as pdf:
            reloaded_img = nib.load(
                f"/tmp/permutation_experiment/{bids_name}"
            )

            reloaded_arr = reloaded_img.get_fdata()

            make_and_show_middle_slices(reloaded_arr.mean(axis=3))
            plt.suptitle("Corrected, mean over time")
            pdf.savefig()
            plt.close()

            make_and_show_middle_slices(reloaded_arr[:, :, :, -1])
            plt.suptitle("Last TR")
            pdf.savefig()
            plt.close()

            ts = reloaded_arr.mean(axis=(0, 1, 2))
            TR = reloaded_img.header["pixdim"][4]
            n_TR = reloaded_arr.shape[-1]
            t_axis = np.linspace(0, TR * n_TR, len(ts))
            plt.plot(t_axis, ts)
            plt.title("Global signal")
            plt.xlabel("Time (s)")
            pdf.savefig()
            plt.close()

            f, Pxx = periodogram(
                ts,
                fs=1/TR
            )
            plt.plot(f, Pxx)
            plt.xlabel('frequency [Hz]')
            plt.ylabel('PSD [V**2/Hz]')
            plt.title("Periodogram")
            pdf.savefig()
            plt.close()

 # Output a report for each outlier,
 # to assess whether reconstruction worked
generate_reports(outliers)

# %%

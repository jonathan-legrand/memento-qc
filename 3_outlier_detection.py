"""
Use an outlier detection algorithm on Image Quality Metrics (IQM)
computed by mriqc to detect bad scans. The SLURM commands used
to generate IQM are stored in participants_mriqc.slurm
"""
# %%
import pandas as pd
import os
from pathlib import Path
from sklearn.ensemble import IsolationForest
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.decomposition import PCA
import nibabel as nib
from bids import BIDSLayout

from matplotlib.backends.backend_pdf import PdfPages

from utils.visualisation import make_and_show_middle_slices
from mappings.iqms import *

MODALITY = "bold"
CENTRE = "all"

# %%
input_path = Path("/georges/memento/BIDS")

qc = pd.read_csv(
    input_path / f"derivatives/mriqc/group_{MODALITY}.tsv",
    sep="\t"
)

participants = pd.read_csv(input_path / "participants.tsv", sep="\t")
qc["participant_id"] = qc["bids_name"].apply(
    lambda x: x.split("_")[0]
)
# Avoid IQMs that discriminate on size and space
cols = summary_bg + summary_fg + structural + afni + ghosts + fd
qc = qc.loc[:, cols + ["participant_id", "bids_name"]]

merged = pd.merge(qc, participants, how="inner").dropna()
if CENTRE != "all":
    merged = merged[merged.centre == CENTRE]


try:
    layout = BIDSLayout(database_path="pybids")
except TypeError: # This is the stupidest thing to raise
    layout = BIDSLayout(
        input_path, 
        validate=False,
        index_metadata=False
    )
# %%

X = merged.select_dtypes(np.number)

pipe = Pipeline(
    [
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=15)),
        ("clf", IsolationForest(random_state=1234))
    ]
)
pipe.fit(X)
y_pred = pipe.predict(X)
X_scores = pipe.decision_function(X)
clf_name = pipe.named_steps['clf'].__str__()

# %% Visualize results in plane using PCA and pairplots
vis_pipe = make_pipeline(
    StandardScaler(),
    Normalizer(),
    PCA()
)
X_reduced = vis_pipe.fit_transform(X)

quality_score = 1 - (X_scores.max() - X_scores) / (X_scores.max() - X_scores.min())

df = pd.DataFrame(X_reduced[:, :4])
df["quality_score"] = quality_score
sns.pairplot(
    df,
    hue="quality_score",
    plot_kws={"s": 7},
    height=2,
    palette="rocket",
    diag_kws=dict(color="gray", hue=None)
)

plt.suptitle(f"{clf_name}", y=1.05)
plt.show()

# %% 
pca = vis_pipe.named_steps["pca"]
plt.bar(range(1, len(pca.components_)+1), np.cumsum(pca.explained_variance_))
plt.vlines(15, 0, 1, color="tab:red", label="PCA cutoff")
plt.xlabel("#Components")
plt.ylabel("Cumulated explained variance")
plt.title("PCA on Image Quality Metrics")
plt.legend()
plt.show()

# %% Sort by quality score

merged["quality_score"] = quality_score 
sorted = merged.sort_values(by="quality_score", ascending=True)
# %% Show outliers

if MODALITY == "bold":
    argnames = ["subject", "session", "task", "suffix"]
else:
    argnames = ["subject", "session", "suffix"]


os.makedirs("output/QC", exist_ok=True)
with PdfPages(
    f"output/QC/{clf_name}_pca_{MODALITY}_{CENTRE}_15comps.pdf"
) as pdf:
    for _, row in sorted[sorted.quality_score < 0.3].iterrows():

        targets = row.bids_name.split("_")
        kwargs = dict(zip(argnames, targets))
        kwargs = {k: v.split("-")[-1] for k, v in kwargs.items()}

        rsfmri = layout.get(**kwargs, extension="nii.gz")[0]

        arr = nib.load(rsfmri.path).get_fdata()

        if MODALITY == "bold":
            make_and_show_middle_slices(arr.mean(axis=3))
        else:
            make_and_show_middle_slices(arr)

        plt.suptitle(
            row.bids_name + " " + row.centre + f" q = {row.quality_score:.2f}")
        pdf.savefig()
        plt.close()

# %% Plot quality score as a function of rank
y = sorted.quality_score.to_numpy()
x = np.arange(len(y))
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(x, y, label="Quality score", color="tab:blue")
ax.plot(
    x, np.ones(len(x)) * 0.1, color="tab:red", label="Threshold")
ax.set_xlabel("Scan rank")
ax.set_ylabel("Quality score")
fig.legend(loc="lower right")
ax.set_title(f"{clf_name} on Memento {MODALITY} IQMs")
plt.show()


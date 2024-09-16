"""
Extracts sample subjects from the MEMENTO dataset to PLAYGROUND_DIR
Typical experiment order would be create_playground -> memento2bids
and then any detection script
"""
# %%
from pathlib import Path
import random
import shutil

MRI_DIR = "/georges/memento/IRM/M000_M024"
PLAYGROUND_DIR = "/scratch/memento_sample"
PATTERN = "**/SUBJ*"
N_SAMPLES = 1

# %% Select N_SAMPLES subjects dir per centre
mri_path = Path(MRI_DIR)
dst_path = Path(PLAYGROUND_DIR)

samples = []

for centre in mri_path.iterdir():
    
    # MacOS is stupid
    if "DS_Store" in centre.stem:
        continue

    matches = (mri_path / centre).glob(PATTERN)
    subject_path = random.sample(tuple(matches), N_SAMPLES)
    samples.append(
        (centre, subject_path)
    )
    

# %% Copy samples to the playground

for centre, subject_collection in samples:
    for subject_path in subject_collection:
        print(subject_path)
    
        shutil.copytree(
            subject_path,
            dst_path / centre.stem / subject_path.stem,
            copy_function=shutil.copy, # We don't need Unix metadata
            dirs_exist_ok=True
        )

# %%

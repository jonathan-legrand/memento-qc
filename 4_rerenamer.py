"""
Revert a name change using name-change files
"""
# %%

import pandas as pd
from pathlib import Path
import os

INPUT_DIR = Path("/scratch/memento_sample_bids")

name_change = pd.read_csv(
    INPUT_DIR / "name-change_2024-09-16_17:23:31.csv",
    index_col=0
)
# %%
for _, row in name_change.iterrows():
    # Yes I made a typo, and the files
    # were generated that way
    os.rename(row.new_path, row.orginal_path)
# %%

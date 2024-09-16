"""
Rename all the input files to add the acq-rejected flag and
exclude from further processing. An input file should
just be a csv file containing the subject and session
columns.
"""
# %%
import pandas as pd
from bids import BIDSLayout
import os
import pandas as pd
from datetime import datetime

INPUT_DIR = "/scratch/memento_sample_bids"

layout = BIDSLayout(INPUT_DIR, validate=False)
# %%
df = pd.read_csv(
    "output/permuted_brains.csv",
    index_col=0,
    dtype={"subject": str}
)

# %%

def add_entity(src, entity="acq", key="rejected"):
    split_path = src.split("/")
    entities = split_path.pop(-1).split("_")
    entities.insert(-1, entity + "-" + key)
    new_fname = "_".join(entities)
    split_path.append(new_fname)
    return "/".join(split_path)

name_matching = []
for _, row in df.iterrows():
    matches = layout.get(
        subject=row.subject, session=row.session
    )

    # There are three files to rename each time:
    # the T1w reference, the bold sequence
    # and the json sidecar
    for match in matches:
        new_path = add_entity(match.path)

        name_matching.append((match.path, new_path))
        os.rename(match.path, new_path)

name_matching = pd.DataFrame(name_matching, columns=["orginal_path", "new_path"])
    
# %% We want to keep track of name changes
# The 'name-change*' pattern should be added to .bidsignore
# to pass bids validation
timestamp = str(datetime.now().strftime('%Y-%m-%d_%H:%M:%S'))
name_matching.to_csv(
    INPUT_DIR + "/name-change_" + timestamp + ".csv"
)


# %%

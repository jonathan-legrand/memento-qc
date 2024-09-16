"""
This script bidsifies the content of the INPUT_DIR,
which should use the memento weird convention,
and put it in the BIDS_DIR.
"""

import nibabel as nib
from pathlib import Path
import os
import json
import warnings
import argparse

from mappings.sidecar import bold_sidecar
from utils.file_matcher import recursive_file_matcher
from utils.memento_structure import extract_info
from gzip import BadGzipFile


class Modality:
    def __init__(self, memento_fnames, bids_modality, bids_suffix, sidecar=None):
        self.memento_name = memento_fnames
        self.bids_modality = bids_modality
        self.suffix = bids_suffix
        self.sidecar = sidecar


def memento_to_bids(
    input_path: Path, 
    bids_path: Path,
    modality: Modality,
    overwrite_participants: bool = False
    ):
    """
    Bidsifies the content of the input_dir,
    which should use the memento convention,
    and put it under the bids_path.
    Args:
        modality (Modality): Object describing the
        modality that's being transfered. For now
        the transfer is done one modality at a time.
    """

    
    gen = recursive_file_matcher(input_path, modality.memento_name)
    if overwrite_participants:
        with open(bids_path / "participants.tsv", "w") as f:
            f.write("participant_id\tcentre\n")

    for fpath in gen:

        # Check and update header
        nifti_img = nib.load(fpath)
        hdr = nifti_img.header

        if hdr["dim"][0] != 4 and modality.bids_modality == "func":
            print(f"{fpath} is not a 4D sequence, skipping to next file.")
            continue
        # Ensure units are written in header
        if modality.bids_modality == "func":
            nifti_img.header.set_xyzt_units(xyz="mm", t="sec")

        # Create arborescense
        site, ses, sub = extract_info(fpath)
        bids_fpath = bids_path / f"sub-{sub}" / f"ses-{ses}" / modality.bids_modality
        bids_fname = f"sub-{sub}_ses-{ses}_{modality.suffix}"
        nifti_dest_fpath = bids_fpath / (bids_fname + ".nii.gz")
        
        if os.path.isfile(nifti_dest_fpath): # Checking earlier could be more efficient
            warnings.warn(f"{nifti_dest_fpath} already exists, nothing has been written")
            continue
        else:
            try:
                os.makedirs(
                    bids_fpath,
                    exist_ok=True
                )
                nib.save(nifti_img, nifti_dest_fpath)
            except BadGzipFile:
                warnings.warn(f"gzip error when saving {nifti_dest_fpath}, skipping scan")
                continue

        # Set repetition time for sidecar, write in dir
        if modality.sidecar is not None:
            modality.sidecar["RepetitionTime"] = float(hdr["pixdim"][4])
            with open(bids_fpath / (bids_fname + ".json"), "w") as f:
                json.dump(modality.sidecar, f)

        # Update participants list if necessary
        with open(bids_path / "participants.tsv", 'r+') as f:
            participant_exists = any(sub in line for line in f)
            if not participant_exists:
                f.write(f"sub-{sub}\t{site}\n")
    
        print(site, bids_fname)


# These could be abstracted further but let's be explicit
def t1w_to_bids(inp, outp):
    from mappings.fnames import ALL_T1_FNAMES
    print("Order of matching :")
    print(ALL_T1_FNAMES)
    for t1_fname in ALL_T1_FNAMES:
        t1 = Modality(
            {t1_fname},
            "anat",
            "T1w"
        )
        memento_to_bids(inp, outp, t1, overwrite_participants=True)

def bold_to_bids(inp, outp):
    from mappings.fnames import ALL_BOLD_FNAMES
    print("Order of matching :")
    print(ALL_BOLD_FNAMES)
    for bold_fname in ALL_BOLD_FNAMES:
        rsfmri = Modality(
            {bold_fname},
            "func",
            "task-rest_bold",
            sidecar=bold_sidecar
        )
        memento_to_bids(inp, outp, rsfmri, overwrite_participants=False)
        
def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="""
        Convert existing datadir using Memento convention into
        BIDS format. Only supports T1w and resting state bold modalities for now.
        """
    )
    parser.add_argument(
        "input_dir",
        help="Path of the input directory containing scans in Memento format."
    )
    parser.add_argument(
        "output_dir",
        help="""
        Path of the output BIDS directory. Directory is created with
        empty BIDS files if it does not exist.
        """
    )
    return parser

if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    input_path = Path(args.input_dir)
    bids_path = Path(args.output_dir)
    
    if not os.path.exists(bids_path):
        print(f"Creating BIDS directory and strucure in {bids_path}")
        os.mkdir(bids_path)
        os.mkdir(bids_path / "derivatives")
        os.mkdir(bids_path / "code")
        os.mkdir(bids_path / "sourcedata")
        open(bids_path / "CHANGES", "w").close()
        open(bids_path / "dataset_description.json", "w").close()
        open(bids_path / "participants.json", "w").close()
        open(bids_path / "participants.tsv", "w").close()
        open(bids_path / "README", "w").close()
        open(bids_path / ".bidsignore", "w").close()

    t1w_to_bids(input_path, bids_path)
    bold_to_bids(input_path, bids_path)



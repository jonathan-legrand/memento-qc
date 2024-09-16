
import nibabel as nib
import numpy as np
from utils.memento_structure import extract_info
    
def sequence_report(nifti_path):
    nifti_img = nib.load(nifti_path)
    
    is_4D = (nifti_img.header["dim"][0] == 4)
    if is_4D:
        Tr = nifti_img.header["pixdim"][4]
    else:
        Tr = np.nan
    centre, month, subject_id = extract_info(nifti_path)

    x, y, z, t = nifti_img.header["dim"][1:5]

    return subject_id, centre, month, is_4D, Tr, nifti_path, x, y, z, t

def sequence_report_with_units(nifti_path):
    nifti_img = nib.load(nifti_path)
    
    is_4D = (nifti_img.header["dim"][0] == 4)
    if is_4D:
        Tr = nifti_img.header["pixdim"][4]
    else:
        Tr = np.nan
    centre, month, subject_id = extract_info(nifti_path)

    x, y, z, t = nifti_img.header["dim"][1:5]
    
    vox_units, time_units = nifti_img.header.get_xyzt_units()

    return subject_id, centre, month, is_4D, Tr, nifti_path, x, y, z, t, vox_units, time_units


import nibabel as nib

def make_st(path):
    """Compute slice timing of a file, assuming
    interleaved acquisition with even slice first
    Args:
        path (_type_): path to bold file

    Returns:
        _type_: list of slice timings
    """
    img = nib.load(path)
    t_r = img.header["pixdim"][4]
    n_slices = img.header["dim"][3]
    seed = [0, t_r / 2]

    if n_slices % 2 == 0:
        slice_timing = seed * (n_slices // 2)
    else:
        slice_timing = seed * (n_slices // 2) + [0]

    return slice_timing
    
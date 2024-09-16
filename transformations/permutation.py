import numpy as np
import nibabel as nib



def destripe_img(bad_img : np.ndarray):
    """
    Vectorized version of unstripping
    function.

    Args:
        bad_img : 4D numpy array containing
        a permuted, carpet like image

    Returns:
        np.ndarray: Rearranged array
    """
    new_arr = np.zeros_like(bad_img)

    n_TR = bad_img.shape[-1]
    z_size = bad_img.shape[2]

    slice_idx : int = 0
    time_idx : int  = 0
    old_t_idx : int = 0
    offset : int = 0

    while slice_idx < z_size:

        while time_idx + z_size <= n_TR:
            print(time_idx)
            new_arr[:, :, slice_idx, time_idx:time_idx+z_size] = bad_img[:, :, :, old_t_idx]
            time_idx += z_size
            old_t_idx += 1

        offset = (n_TR - z_size + offset) % z_size

        # If the current slice has been perfectly filled with the current
        # channel, jump to next slice
        if offset == 0:
            slice_idx += 1
            time_idx = 0

        # Complete current slice up to the offset and start the next slice with what's left
        else:
            print(f"Filling slice {slice_idx}, offset = {offset}", time_idx)
            new_arr[:, :, slice_idx, time_idx:time_idx+offset] = bad_img[:, :, :offset, old_t_idx]

            slice_idx += 1

            # Fill the next slice with the rest of the old channel
            # only if the top of the volume has not been reached
            if slice_idx < z_size:
                time_idx = 0
                new_arr[:, :, slice_idx, time_idx:(z_size - offset)] = bad_img[:, :, offset:, old_t_idx]
                time_idx += z_size - offset
                old_t_idx += 1
    
    return new_arr

def convert_outliers(outliers, layout, overwrite_bids=False):
    for _, s in outliers.iterrows():
        bad_rsfmri = layout.get(
            subject=s.participant_id[4:],
            session=s.session,
            suffix="bold",
            extension="nii.gz"
        )[0]
        bad_img = nib.load(bad_rsfmri.path)

        new_arr = destripe_img(bad_img.get_fdata())
        new_img = nib.Nifti1Image(new_arr, bad_img.affine, bad_img.header)
        if overwrite_bids:
            nib.save(new_img, bad_rsfmri.path)
        else:
            nib.save(
                new_img,
                f"/tmp/permutation_experiment/{bad_rsfmri.filename}"
            )


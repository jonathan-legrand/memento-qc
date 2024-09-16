from scipy.spatial import distance
import nibabel as nib
from nibabel.affines import apply_affine


def image_centre(img):
    if img.ndim == 4:
        h, w, d, _ = img.shape
    else:
        h, w, d = img.shape
    return h/2, w/2, d/2

def distance_between_FOVs(
    reference_img: nib.filebasedimages.FileBasedImage,
    epi_img: nib.filebasedimages.FileBasedImage
):
    ref_centre_scanner = apply_affine(
        reference_img.affine,
        image_centre(reference_img)
    )
    epi_centre_scanner = apply_affine(
        epi_img.affine,
        image_centre(epi_img)
    )
    return distance.euclidean(ref_centre_scanner, epi_centre_scanner)
from scipy.signal import convolve2d
import numpy as np

sobel_x = np.array([
    [1, 0, -1],
    [2, 0, -2],
    [1, 0, -1]
])

def middle_gradients_qa(vol):
    """Permuted images should have
    low gradient magnitudes in the
    direction of the stripes.
    To detect them, we compute
    the absolute value of the 
    derivative along this axis
    

    Args:
        vol (_type_): _description_

    Returns:
        _type_: _description_
    """
    if vol.ndim == 4:
        vol = vol.mean(axis=3)
    elif vol.ndim != 3:
        raise ValueError(f"Array has {vol.ndim} dimensions instead of 3 or 4.")
        
    h, w, d = vol.shape 
    
    images = (
        ("sagittal", vol[h//2, :, :]),
        ("coronal", vol[:, w//2, :]),
        ("transverse", vol[:, :, d//2],)
    )

    # No point in yielding
    qa_measures = []
    for plane, image in images:
        gradient_magnitude = abs(convolve2d(image, sobel_x, boundary="symm", mode="same"))
        sog = gradient_magnitude.sum() / image.std()
        qa_measures.append((plane, sog))
    return qa_measures
        
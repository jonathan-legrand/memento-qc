import numpy as np

def efc(img, framemask=None):
    r"""
    Calculate the :abbr:`EFC (Entropy Focus Criterion)` [Atkinson1997]_.
    Uses the Shannon entropy of voxel intensities as an indication of ghosting
    and blurring induced by head motion. A range of low values is better,
    with EFC = 0 for all the energy concentrated in one pixel.

    .. math::

        \text{E} = - \sum_{j=1}^N \frac{x_j}{x_\text{max}}
        \ln \left[\frac{x_j}{x_\text{max}}\right]

    with :math:`x_\text{max} = \sqrt{\sum_{j=1}^N x^2_j}`.

    The original equation is normalized by the maximum entropy, so that the
    :abbr:`EFC (Entropy Focus Criterion)` can be compared across images with
    different dimensions:

    .. math::

        \text{EFC} = \left( \frac{N}{\sqrt{N}} \, \log{\sqrt{N}^{-1}} \right) \text{E}

    :param numpy.ndarray img: input data
    :param numpy.ndarray framemask: a mask of empty voxels inserted after a rotation of
      data

    """

    if framemask is None:
        framemask = np.zeros_like(img, dtype=np.uint8)

    n_vox = np.sum(1 - framemask)
    # Calculate the maximum value of the EFC (which occurs any time all
    # voxels have the same value)
    efc_max = 1.0 * n_vox * (1.0 / np.sqrt(n_vox)) * np.log(1.0 / np.sqrt(n_vox))

    # Calculate the total image energy
    b_max = np.sqrt((img[framemask == 0] ** 2).sum())

    # Calculate EFC (add 1e-16 to the image data to keep log happy)
    return float(
        (1.0 / efc_max)
        * np.sum((img[framemask == 0] / b_max) * np.log((img[framemask == 0] + 1e-16) / b_max))
    )
from scipy import signal
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt

def make_slice_corr_map(sequence_array):
    slice_signals = signal.detrend(sequence_array.mean(axis=(0, 1)), axis=1)
    mat = slice_signals - slice_signals.mean(axis=1).reshape((len(slice_signals), 1))
    mat /= mat.std(axis=1).reshape((len(mat), 1))
    corr_map = mat @ mat.T / slice_signals.shape[1]
    return mat, corr_map

# Too much responsability on this 
# poor function
def odd_slices_lag(
    signals,
    os_factor=10,
    display=True
):
    """Computes the lag between odd slices and 
    even slices, due to potential interleaved
    acquisition

    Args:
        signals (_type_): Array of zcored and detrended
        signals, of shape (slice, time)
        os_factor (int, optional): Oversampling
        factor. Defaults to 10.

    Returns:
        int: Optimal cross correlation lag, in TR
    """
    
    t_TR = np.linspace(0, signals.shape[1], signals.shape[1])

    res, res_t = signal.resample(
        signals,
        num=os_factor*signals.shape[1],
        t=t_TR,
        axis=1
    )

    even_signals = res[::2, :]
    odd_signals = res[1::2, :]
    corr = signal.correlate(
        even_signals.mean(axis=0), 
        odd_signals.mean(axis=0),
        mode="same"
    ) / even_signals.shape[1]
    lags = signal.correlation_lags(
        even_signals.shape[1],
        odd_signals.shape[1],
        mode="same"
    )
    tau_opt = lags[np.argmax(corr)]

    if display is True:
        fig, axes = plt.subplots(2, 1, figsize=(10, 10))

        fig.suptitle("Slice signals")
        axes[0].plot(t_TR, signals.T)
        axes[0].set_title("Original, T_s = TR s")
        axes[0].set_xlabel("Time (TR)")

        axes[1].plot(res_t, res.T)
        axes[1].set_title(f"Oversampled, T_s = TR / {os_factor} s")
        axes[1].set_xlabel("Time (TR)")
        plt.show()

        plt.plot(
            res_t,
            even_signals.mean(axis=0), label="Even slices"
        )
        plt.plot(
            res_t,
            odd_signals.mean(axis=0),
            label="Odd slices",
            color="tab:orange"
        )
        plt.title("Oversampled mean slice signals")
        plt.legend()
        plt.show()


        plt.plot(lags / os_factor, corr)
        plt.xlabel("Lag (TR)")
        plt.ylabel("Correlation")
        plt.title(f"Even-Odd cross correlation\n\
        tau_opt = {tau_opt / os_factor} TR")
        plt.show()

    return tau_opt / os_factor

def rsfmri_lag(rsfmri_path, display=False):
    img = nib.load(rsfmri_path).get_fdata()
    # TODO We don't need to compute the matrix
    signals, _ = make_slice_corr_map(img)
    return odd_slices_lag(signals, display=display)
import matplotlib.pyplot as plt
import numpy as np

# TODO Allow TR and n_slices configuration
def show_slice_timing(timing_lst, TR=0.85):
    f, ax = plt.subplots(figsize=(8, 8))
    n_slices = len(timing_lst)
    ax.scatter(
        x=np.linspace(1, n_slices, n_slices),
        y=timing_lst,
        label="Slice excitation"
    )
    ax.plot([0, n_slices], [TR, TR], color='red', label="t = TR")
    ax.plot([0, n_slices], [0, 0], color='green', label="t = 0")
    ax.set_ylabel("Time (s)")
    ax.set_xlabel("Slice index")
    ax.legend(loc="upper right")
    return f
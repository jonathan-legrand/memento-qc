import matplotlib.pyplot as plt
import random
import numpy as np
import seaborn as sns


def show_slices(slices):
    
    """ Function to display column of image slices """
    
    names = ("saggital", "coronal", "axial")
    fig, axes = plt.subplots(len(slices), figsize=(10, 10))
    
    for i, slice in enumerate(slices):
    
        axes[i].imshow(slice.T, cmap="gray", origin="lower")
        axes[i].set_title(names[i])
        
    return fig


def make_and_show_middle_slices(volume):
    """
    Stupid name
    """
    if volume.ndim == 4:
        volume = volume.mean(axis=3)
    h, w, d = volume.shape
    return show_slices(
        (
            volume[h//2, :, :],
            volume[:, w//2, :],
            volume[:, :, d//2]
        )
    )

def biplot(score, coeff , y, varnames, norm_treshold=0.2, eps=1e-1):
    '''
    Author: Serafeim Loukas, serafeim.loukas@epfl.ch
    Inputs:
       score: the projected data
       coeff: the eigenvectors (PCs)
       y: the class labels
   '''    
    xs = score[:,0] # projection on PC1
    ys = score[:,1] # projection on PC2
    n = coeff.shape[0] # number of variables
    _, axes = plt.subplots(2, 1, dpi=100, figsize=(10, 15))
    
    
    classes = np.unique(y)
    #colors = sns.color_palette(n_colors=len(classes))
    for s,l in enumerate(classes):
        axes[0].scatter(xs[y==l],ys[y==l]) # color based on group
    for i in range(n):
        #plot as arrows the variable scores (each variable has a score for PC1 and one for PC2)
        offset = random.random() * eps
        
        if np.sqrt(coeff[i, 0]**2 + coeff[i, 1]**2) > norm_treshold:
            axes[1].arrow(
                0,
                0,
                coeff[i,0],
                coeff[i,1],
                color = 'k',
                alpha = 0.9,
                linestyle = '-',
                linewidth = 1.5,
                overhang=0.2
            )
            axes[1].text(
                coeff[i,0]* 1.2 + offset,
                coeff[i,1] * 1.2 + offset,
                varnames[i],
                color = 'k',
                ha='center',
                va='center',
                fontsize=10
            )

    plt.xlabel("PC{}".format(1), size=14)
    plt.ylabel("PC{}".format(2), size=14)
    limx= int(xs.max()) + 1
    limy= int(ys.max()) + 1
    plt.xlim([-limx,limx])
    plt.ylim([-limy,limy])
    plt.grid()
    plt.tick_params(axis='both', which='both', labelsize=14)
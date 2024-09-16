import numpy as np

# Correction attempt, very C-like, but it seems to be working
# TODO Retest, hasn't been tested since it has been refactored into
# a function 

def destripe_img_old(bad_img):
    last_dim_idx : int = 0
    old_time_idx : int = 0
    counter : int = 0
    new_arr = np.zeros_like(bad_img)
    
    n_TR = bad_img.shape[-1]
    z_size = bad_img.shape[2]
    
    slice_idx = 0
    while slice_idx < z_size:
        while last_dim_idx < n_TR:
            
            while old_time_idx < z_size:
            
                new_arr[:, :, slice_idx, counter] = bad_img[:, :, old_time_idx, last_dim_idx]
    
                old_time_idx += 1
                counter += 1
    
                if counter == n_TR:
                    counter = 0
                    slice_idx += 1
                    print(
                        f"Jump to slice {slice_idx}, z_idx = {old_time_idx}, t_idx = {last_dim_idx}"
                    )
    
                
            old_time_idx = 0
            last_dim_idx += 1
        
        old_time_idx = 0
        last_dim_idx = 0
    return new_arr
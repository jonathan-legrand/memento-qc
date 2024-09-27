# Script used to launch the preprocessing pipeline of the whole memento cohort in pipeau
#!/bin/bash

#SBATCH -J fmriprep
#SBATCH --partition highmem
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=8G
# Outputs ----------------------------------
#SBATCH -o log/%x-%A-%a.out
#SBATCH -e log/%x-%A-%a.err
# ------------------------------------------

STUDY="/beegfs_data/scratch/jlegrand-memento_preprocessing"
BIDS_DIR="$STUDY/BIDS"
DERIVS_DIR="derivatives/fmriprep-23.2.0"

# Prepare some writeable bind-mount points.
TEMPLATEFLOW_HOST_HOME=$HOME/.cache/templateflow
FMRIPREP_HOST_CACHE=$HOME/.cache/fmriprep
mkdir -p ${TEMPLATEFLOW_HOST_HOME}
mkdir -p ${FMRIPREP_HOST_CACHE}

# Prepare derivatives folder
mkdir -p ${BIDS_DIR}/${DERIVS_DIR}

# Make sure FS_LICENSE is defined in the container.
export SINGULARITYENV_FS_LICENSE=$HOME/license.txt

# Designate a templateflow bind-mount point
export SINGULARITYENV_TEMPLATEFLOW_HOME="/templateflow"
SINGULARITY_CMD="singularity run --cleanenv -B $BIDS_DIR:/data -B ${TEMPLATEFLOW_HOST_HOME}:${SINGULARITYENV_TEMPLATEFLOW_HOME} /homes_unix/jlegrand/Images/fmriprep-latest.simg"

# Parse the participants.tsv file and extract one subject ID from the line corresponding to this SLURM task.
subject=$( sed -n -E "$((${SLURM_ARRAY_TASK_ID} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )

## Compose the command line
cmd="${SINGULARITY_CMD} /data /data/${DERIVS_DIR} participant \
--skip-bids-validation \
--participant-label $subject \
--bids-filter-file /data/code/filter-bad-acq.json \
--mem_mb 8000 \
--nthreads 4 \
--longitudinal \
--output-spaces MNI152NLin2009cAsym MNI152NLin6Asym:res-2"

# Setup done, run the command
echo Running task ${SLURM_ARRAY_TASK_ID}
echo Commandline: $cmd
eval $cmd
exitcode=$?

# Output results to a table
echo "sub-$subject    ${SLURM_ARRAY_TASK_ID}    $exitcode" \
      >> $STUDY/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${SLURM_ARRAY_TASK_ID} with exit code $exitcode
exit $exitcode
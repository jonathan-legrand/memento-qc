#!/bin/bash
#
#SBATCH -J mriqc
#SBATCH --time=04:00:00
#SBATCH -n 1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=8G
# Outputs ----------------------------------
#SBATCH -o log/%x-%A-%a.out
#SBATCH -e log/%x-%A-%a.err
#SBATCH --mail-user=jonathan.legrand@u-bordeaux.fr
#SBATCH --mail-type=ALL
# ------------------------------------------

BIDS_DIR="$STUDY/BIDS"
DERIVS_DIR="derivatives/mriqc"

# Prepare derivatives folder
mkdir -p ${BIDS_DIR}/${DERIVS_DIR}

# Parse the participants.tsv file and extract one subject ID from the line corresponding to this SLURM task.
subject=$( sed -n -E "$((${SLURM_ARRAY_TASK_ID} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )

SINGULARITY_CMD="singularity run --cleanenv -B $BIDS_DIR:/data ~/data/mriqc-latest.simg"

# Compose the command line
cmd="${SINGULARITY_CMD} /data /data/${DERIVS_DIR} participant \
--participant-label $subject \
--modalities T1w bold \
-w ~/Runs/Slurm/ -vv --mem_gb 8 --nprocs 4"

# Setup done, run the command
module load singularity
echo Running task ${SLURM_ARRAY_TASK_ID}
echo Commandline: $cmd
eval $cmd
exitcode=$?

# Output results to a table
echo "sub-$subject   ${SLURM_ARRAY_TASK_ID}    $exitcode" \
      >> ~/Runs/Slurm/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${SLURM_ARRAY_TASK_ID} with exit code $exitcode
exit $exitcode


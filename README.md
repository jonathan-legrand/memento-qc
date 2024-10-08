# Memento QC and formatting

This repository gathers scripts and functions used
for all operations prior to fMRI preprocessing in Memento.
Includes generating reports on existing files,
switching to BIDS, removing improperly formatted files
and performing automated QC.

Most of the scripts were run using vscode's extension for
jupyter-like cells, hence the `# %%` tags.

Scripts starting with 1, 2, 4 and 7 are able to write to BIDS directory,
make sure you understand what they do before executing them.

To get started, create a conda environment with proper dependencies
using `conda env create -f environment.yml`.
You may also need to create a directlory named `output`
at the root of the project, that will be used by scripts
to export csv files and pdf reports.

## Quality control

The logic of QC is that all the scripts starting by 3 are
able to detect bad scans. The ones that cannot be repaired
are excluded from the preprocessing using the renamer 
script, which takes a csv file containing the subject and session
columns as an input and adds the `acq-rejected` flag to their bids name. These scans are then filtered out using bids [filter files](https://fmriprep.org/en/24.0.1/faq.html#how-do-i-select-only-certain-files-to-be-input-to-fmriprep) when calling fMRIprep. In case you want to revert a name change, `4_rerename.py`is here for you.

The document `IRMf dans Memento - rapport d'avancement.pdf`
reports the choices that have been made regarding which scans
were kept and which ones were rejected.

## Slice timing

Slice timing information is missing in Memento, so we need
to guess it, using the lag between odd and even slices, and
the `cati_monito` file which maps scans to machines.
Scripts 5, 6 and 7 handle slice timing inference
and generation.

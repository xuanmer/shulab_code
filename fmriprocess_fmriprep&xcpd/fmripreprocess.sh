# Rsting-stat fmri preprocess based on fmriprep (https://fmriprep.org/en/stable/) and xcp-d (https://xcp-d.readthedocs.io/en/latest/index.html)
# The process includs:
# 1. Remove first 8 dummy scans
# 2. Head motion estimation and correction
# 3. Slice timing correction
# 4. Susceptibility distortion correction (if no filedmap use fieldmap-less susceptibility-derived distortions estimation)
# 5. Spatial normalization
# 6. Confounds estimation
docker run -ti --rm \
    -v /home/shulab/bty/fmri_xcpd/data:/data \
    -v /home/shulab/bty/fmri_xcpd/output/fmriprep:/out \
    -v /home/shulab/bty/fmri_xcpd/codes/license.txt:/opt/freesurfer/license.txt \
    nipreps/fmriprep:23.2.3 \
    /data /out participant \
    --slice-time-ref 0.5 \
    --dummy-scans 8 \
    --use-syn-sdc \
    --output-spaces MNI152NLin2009cAsym \
    --fs-no-reconall \
    --no-submm-recon \
    --ignore fieldmaps \
    --random-seed 42 
# 7. Detrend
# 8. Confounds regression with 36P
# 9. Bandpass filtering (0.01-0.08 Hz)
# 10. Estimate FC matrix
docker run --rm -it \
  -v /home/shulab/bty/fmri_xcpd/output/fmriprep:/fmriprep:ro \
  -v /home/shulab/bty/fmri_xcpd/output/xcpd/wkdir:/work:rw \
  -v /home/shulab/bty/fmri_xcpd/output/xcpd:/out:rw \
  -v /home/shulab/bty/fmri_xcpd/codes:/codes \
  pennlinc/xcp_d:latest \
  --mode none \
  /fmriprep /out participant \
  --datasets schafer=/fmriprep/atlases/schaefer \
  --atlases Schaefer1000 \
  --fs-license-file /codes/license.txt \
  --input-type fmriprep \
  --file-format nifti \
  --nuisance-regressors 36P \
  --despike n \
  --abcc-qc y \
  --linc-qc n \
  --combine-runs n \
  --fd-thresh 0 \
  --min-coverage 0.2 \
  --motion-filter-type none \
  --output-type censored \
  --warp-surfaces-native2std n \
  --smoothing 6 \
  --random-seed 42 \
  --create-matrices all
#  
docker run --rm -it \
  -v /home/shulab/bty/fmri_xcpd/output/fmriprep:/fmriprep:ro \
  -v /home/shulab/bty/fmri_xcpd/output/xcpd1/wkdir:/work:rw \
  -v /home/shulab/bty/fmri_xcpd/output/xcpd1:/out:rw \
  -v /home/shulab/bty/fmri_xcpd/codes:/codes \
  pennlinc/xcp_d:latest \
  --mode none \
  /fmriprep /out participant \
  --datasets schafer=/fmriprep/atlases/schaefer \
  --atlases Schaefer1000 \
  --fs-license-file /codes/license.txt \
  --input-type fmriprep \
  --file-format nifti \
  --nuisance-regressors 36P \
  --despike n \
  --abcc-qc y \
  --linc-qc n \
  --combine-runs n \
  --fd-thresh 0 \
  --min-coverage 0.2 \
  --motion-filter-type none \
  --output-type censored \
  --warp-surfaces-native2std n \
  --smoothing 6 \
  --random-seed 42 \
  --create-matrices all
# Usage: fmri_preprocess.sh <input> <output> <atlas> 
# <input> is the path to the input folder with BIDS formation
# it will be organized like this:
#  - sub-0001
#    - anat
#      - sub-0001_T1w.nii.gz
#      - sub-0001_T1w.json
#    - func
#      - sub-0001_task-rest_bold.nii.gz
#      - sub-0001_task-rest_bold.json
# <output> is the path to the output folder
# <atlas> is the path to the atlas file

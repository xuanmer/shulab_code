# bids data
# .
# ├── dataset_description.json
# └── sub-1000037
#     ├── anat
#     │   ├── sub-1000037_T1w.json
#     │   └── sub-1000037_T1w.nii.gz
#     └── func
#         ├── sub-1000037_task-rest_bold.json
#         └── sub-1000037_task-rest_bold.nii.gz

# 3 directories, 5 files

docker run -it --rm --gpus all \
             -v /home/shulab/bty/deepprep/data:/input \
             -v /home/shulab/bty/deepprep/output1:/output \
             -v /home/shulab/bty/license.txt:/fs_license.txt \
             pbfslab/deepprep:25.1.0 \
             /input \
             /output \
             participant \
             --bold_task_type rest \
             --fs_license_file /fs_license.txt \
             --bold_volume_res 02 \
             --bold_skip_frame 8 \
             --bold_sdc FALSE \
             --bold_volume_space 
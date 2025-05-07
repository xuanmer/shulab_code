# get NC FA mean skeleton mask

# .
# ├── FA
# ├── MD
# ├── NC_FA
# └── stats

NC_FA_DIR="./NC_FA"
stats_DIR="./stats"

mkdir -p "$stats_DIR"
cd "$stats_DIR" 

# 1. merge NC FA images
fslmerg -t all_NC_FA "$NC_FA_DIR"/*_FA_in_MNI.nii.gz 

# 2. create mean skeleton
fslmaths all_NC_FA -Tmean mean_NC_FA

# 3. create mean FA mask (ukb method)
fslmaths mean_NC_FA -bin -mul "$FSLDIR"/data/standard/FMRIB58_FA_1mm -bin mean_NC_FA_mask

# 4. create mean FA skeleton
fslmaths "$FSLDIR"/data/standard/FMRIB58_FA-skeleton_1mm -mas mean_NC_FA_mask mean_NC_FA_skeleton

# 5. create mean FA skeleton mask
thresh=0.2
fslmaths mean_NC_FA_skeleton -thr "$thresh" -bin mean_NC_FA_skeleton_mask

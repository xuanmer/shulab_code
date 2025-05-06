# This script is modified based on the UK biobank script.
# This script did not performed GDC correction because we don't have the grad coef file which is necessary for
# GDC correction and can be obtained from MR manufacturers
templ=${0%/*}/templates

input=$1
output=$2
atlas=$3

if [ ! -e $output/anat ]; then
  mkdir -p $output/anat
fi

# Reduce the fov

t1file=`ls $input/anat/data.nii*`
head_bot=`${FSLDIR}/bin/robustfov -i $t1file | grep -v Final | head -n 1 | awk '{print $5}'`
${FSLDIR}/bin/fslmaths $t1file -roi 0 -1 0 -1 $head_bot -1 0 1 $output/anat/T1_tmp
${FSLDIR}/bin/bet $output/anat/T1_tmp.nii.gz $output/anat/T1_tmp_brain.nii.gz -R

${FSLDIR}/bin/standard_space_roi $output/anat/T1_tmp_brain $output/anat/T1_tmp2 -maskNONE -ssref $FSLDIR/data/standard/MNI152_T1_1mm_brain -altinput $t1file -d


${FSLDIR}/bin/immv $output/anat/T1_tmp2 $output/anat/T1

# registrate the cut version of T1 to MNI 

${FSLDIR}/bin/flirt -in $output/anat/T1 -ref $t1file -omat $output/anat/T1_to_T1_orig.mat -schedule $FSLDIR/etc/flirtsch/xyztrans.sch 
## ${FSLDIR}/bin/convert_xfm -omat  $output/anat/T1_orig_to_T1.mat -inverse  $output/anat/T1_to_T1_orig.mat
${FSLDIR}/bin/convert_xfm -omat  $output/anat/T1_to_MNI_linear.mat -concat  $output/anat/T1_tmp2_tmp_to_std.mat  $output/anat/T1_to_T1_orig.mat


${FSLDIR}/bin/fnirt --in=$output/anat/T1 --ref=$FSLDIR/data/standard/MNI152_T1_1mm --aff=$output/anat/T1_to_MNI_linear.mat --config=${0%/*}/bb_data/bb_fnirt.cnf --refmask=$templ/MNI152_T1_1mm_brain_mask_dil_GD7 --logout=$output/anat/bb_T1_to_MNI_fnirt.log --cout=$output/anat/T1_to_MNI_warp_coef --fout=$output/anat/T1_to_MNI_warp --jout=$output/anat/T1_to_MNI_warp_jac --iout=$output/anat/T1_tmp4.nii.gz --interp=spline


## ${FSLDIR}/bin/convertwarp --ref=$FSLDIR/data/standard/MNI152_T1_1mm --premat=$output/anat/T1_orig_to_T1.mat --warp1=$output/anat/T1_to_MNI_warp --out=$output/anat/T1_orig_to_MNI_warp
## ${FSLDIR}/bin/applywarp --rel -i $t1file -r $FSLDIR/data/standard/MNI152_T1_1mm -w  $output/anat/T1_orig_to_MNI_warp -o  $output/anat/T1_brain_to_MNI --interp=spline


# Create brain mask

${FSLDIR}/bin/invwarp --ref=$output/anat/T1 -w  $output/anat/T1_to_MNI_warp_coef -o  $output/anat/T1_to_MNI_warp_coef_inv
${FSLDIR}/bin/applywarp --rel --interp=trilinear --in=$templ/MNI152_T1_1mm_brain_mask --ref=$output/anat/T1 -w  $output/anat/T1_to_MNI_warp_coef_inv -o  $output/anat/T1_brain_mask
${FSLDIR}/bin/fslmaths  $output/anat/T1 -mul  $output/anat/T1_brain_mask  $output/anat/T1_brain

## ${FSLDIR}/bin/fslmaths  $output/anat/T1_brain_to_MNI -mul $templ/MNI152_T1_1mm_brain_mask  $output/anat/T1_brain_to_MNI


rm  $output/anat/*tmp*
mkdir  $output/anat/transforms
mv  $output/anat/*MNI*  $output/anat/transforms
## mv  $output/anat/*warp*.*  $output/anat/transforms
## mv  $output/anat/*_to_*  $output/anat/transforms
## mv  $output/anat/transforms/T1_brain_to_MNI.nii.gz  $output/anat/

# run fast for tissue segmentation

mkdir  $output/anat/T1_fast
${FSLDIR}/bin/fast -b -o  $output/anat/T1_fast/T1_brain  $output/anat/T1_brain

## ${FSLDIR}/bin/fsl_reg $output/anat/T1_fast/T1_brain_pve_1 ${FSLDIR}/data/standard/tissuepriors/avg152T1_gray $output/anat/T1_fast/T1_GM_to_MNI -fnirt "--config=GM_2_MNI152GM_2mm.cnf --jout=$output/anat/T1_fast/T1_GM_to_MNI_JAC_nl"
## $FSLDIR/bin/fslmaths $output/anat/T1_fast/T1_GM_to_MNI -mul $output/anat/T1_fast/T1_GM_to_MNI_JAC_nl $output/anat/T1_GM_to_MNI_mod -odt float

## echo -e "1 0 0 0\n 0 1 0 0\n 0 0 1 0\n 0 0 0 1" > $output/anat/eyes.mat
## ${FSLDIR}/bin/flirt -in $atlas -ref ${FSLDIR}/data/standard/MNI152_T1_2mm.nii.gz -applyxfm -init $output/anat/eyes.mat -out ${atlas%1mm.nii.gz*}2mm.nii.gz
## 3dresample -input $atlas -dxyz 2 2 2 -prefix ${atlas%1mm.nii.gz*}2mm.nii.gz
## 3dROIstats -mask ${atlas%1mm.nii.gz*}2mm.nii.gz -nobriklab -nzmean -nzvolume $output/anat/T1_GM_to_MNI_mod.nii.gz > $output/anat/gm_vol.txt

atlas_name=${atlas##*/}
echo $atlas
${FSLDIR}/bin/applywarp --rel --interp=nn --in=$atlas --ref=$output/anat/T1 -w $output/anat/transforms/T1_to_MNI_warp_coef_inv -o $output/anat/${atlas_name%.nii.gz*}_native.nii.gz
3dROIstats -mask $output/anat/${atlas_name%.nii.gz*}_native.nii.gz -nobriklab -nzmean -nzvolume $output/anat/T1_fast/T1_brain_pve_1.nii.gz > $output/anat/gm_vol_${atlas_name%.nii.gz*}.txt
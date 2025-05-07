#!/bin/bash

input=$1
output=$2

if [ ! -e $output ]; then
  mkdir -p $output
fi

t1file=`ls $input/anat/*.nii*`

export SUBJECTS_DIR=$output
recon-all -all -s FS -i $t1file
#!/bin/bash

source_dir="/media/shulab/Getea/zhe2/NC/sorted/"
target_dir="/media/shulab/Getea/zhe2/NC/tbss/FA/"

# 创建目标目录（如果不存在）
mkdir -p "$target_dir"

# 遍历每个被试目录
for subj_dir in "$source_dir"*; do
    if [ -d "$subj_dir" ]; then
        subj_id=$(basename "$subj_dir")
        fa_file_path="$subj_dir/dwi/FA_in_MNI.nii.gz"
        
        # 检查文件是否存在
        if [ -f "$fa_file_path" ]; then
            new_file_name="NC_${subj_id}_FA_in_MNI.nii.gz"
            new_file_path="$target_dir$new_file_name"
            cp "$fa_file_path" "$new_file_path"
            echo "成功复制：$fa_file_path 到 $new_file_path"
        else
            echo "警告：未找到文件 $fa_file_path，跳过处理 $subj_id"
        fi
    fi
done

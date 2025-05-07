#!/usr/bin/env bash

# 配置
INPUT_DIR="/media/shulab/Getea/zhe2/NC/tbss/FA"
MASK1="/media/shulab/Getea/zhe2/NC/tbss/stats/mean_CN_FA_mask.nii.gz"
MASK2="/media/shulab/Getea/zhe2/NC/tbss/stats/mean_CN_FA_skeleton_mask.nii.gz"
JHU_ATLAS="${FSLDIR}/data/atlases/JHU/JHU-ICBM-labels-1mm.nii.gz"
MAX_JOBS=10  # 最大并发任务数（建议设为CPU核心数）


# 初始化任务计数器
jobs=0

# 遍历所有FA文件
find "$INPUT_DIR" -maxdepth 1 -name "*.nii.gz" | while read -r fa_file; do
    fa_base=$(basename "$fa_file" .nii.gz)
    masked_file="${INPUT_DIR}/${fa_base}_masked.nii.gz"
    skeleton_file="${INPUT_DIR}/${fa_base}_skeletonised.nii.gz"
    stats_file="${INPUT_DIR}/${fa_base}_JHUrois.txt"
    # 后台执行处理任务
    {
        echo "开始处理: $fa_file"
        command="fslmaths $fa_file -mas $MASK1 $masked_file"
        echo "执行命令: $command"
        eval $command
        command="fslmaths $masked_file -mas $MASK2 $skeleton_file"
        echo "执行命令: $command"
        eval $command
        
        command="fslstats -K $JHU_ATLAS $skeleton_file -M > $stats_file"
        echo "执行命令: $command"
        eval $command
        # 检查文件是否存在且非空
        if [ -s "$JHU_ATLAS" ] && [ -s "$skeleton_file" ]; then
            command="fslstats -K $JHU_ATLAS $skeleton_file -M > $stats_file"
            echo "执行命令: $command"
            eval $command
        else
            echo "错误: $JHU_ATLAS 或 $skeleton_file 为空或不存在"
        fi
        echo "完成处理: $fa_file"
    } &  # 放入后台执行

    jobs=$((jobs + 1))
    
    # 控制最大并发数
    if [ "$jobs" -ge "$MAX_JOBS" ]; then
        wait -n  # 等待任意一个后台任务完成
        jobs=$((jobs - 1))
    fi
done

# 等待所有后台任务完成
wait
echo "所有任务处理完成"
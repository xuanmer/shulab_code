#!/bin/bash

# 最大线程数（可根据需要调整）
MAX_THREADS=40
# 使用绝对路径获取当前脚本所在目录
SCRIPT_DIR=$(dirname "$(realpath "$0")")
# 输入目录（所有被试数据所在目录）
INPUT_DIR="/media/shulab/Getea/zhe2/NC/sorted"
# 输出目录（结果保存路径）
OUTPUT_DIR="/media/shulab/Getea/zhe2/NC/results"
# 图谱文件路径（根据实际情况修改）
ATLAS="$SCRIPT_DIR/atlas/desikan-killiany_1mm.nii.gz"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 初始化线程计数器
THREAD_COUNT=0

# 遍历所有被试文件夹（排除当前目录本身）
find "$INPUT_DIR" -mindepth 1 -maxdepth 1 -type d -name '*' | while read -r subject_folder; do
    subject_id=$(basename "$subject_folder")
    echo "Processing subject: $subject_id"

    # 生成完整的命令行
    cmd="$SCRIPT_DIR/t1_preprocess.sh '$subject_folder' '$OUTPUT_DIR/$subject_id' '$ATLAS'"
    echo "Executing command: $cmd"

    # 调用预处理脚本
    eval "$cmd" &

    ((THREAD_COUNT++))

    # 控制并发线程数
    if [ "$THREAD_COUNT" -ge "$MAX_THREADS" ]; then
        wait -n
        ((THREAD_COUNT--))
    fi
done

# 等待所有任务完成
wait

echo "All subjects processed."
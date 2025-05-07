#!/bin/bash

# 定义主函数
main() {
    max_workers=$1
    base_dir="/media/shulab/Getea/zhe2/NC/sorted/"
    pids=()

    # 遍历所有主题目录
    for subject in "$base_dir"/*; do
        if [ -d "$subject" ]; then
            dwi_dir="$subject/dwi"
            output_dir="$dwi_dir/dtifit"
            log_file="$output_dir/dtifit.log"
            data="$dwi_dir/data_ud.nii.gz"
            mask="$dwi_dir/raw/b0_brain_mask.nii.gz"
            bvec_file="$dwi_dir/bvecs"
            bval_file="$dwi_dir/bvals"

            # 创建 dtifit 文件夹（如果不存在）
            if [ ! -d "$output_dir" ]; then
                mkdir -p "$output_dir"
                if [ $? -ne 0 ]; then
                    echo "Error creating dtifit directory in $dwi_dir"
                    continue
                else
                    echo "Created dtifit directory in $dwi_dir"
                fi
            fi

            echo "Running dtifit on $subject"
            command=(
                dtifit
                "--data=$data"
                "--out=$output_dir/dti"
                "--mask=$mask"
                "--bvecs=$bvec_file"
                "--bvals=$bval_file"
                "--save_tensor"
            )

            # 执行命令并放入后台
            "${command[@]}" > "$log_file" 2>&1 &
            pids+=($!)

            # 控制并发数量
            if [ ${#pids[@]} -ge $max_workers ]; then
                wait -n
                for pid in "${!pids[@]}"; do
                    if ! kill -0 "${pids[$pid]}" 2>/dev/null; then
                        unset pids[$pid]
                    fi
                done
                pids=("${pids[@]}")
            fi
        fi
    done

    # 等待所有后台任务完成
    wait
}

# 可根据需要修改最大线程数
max_workers=10
main $max_workers

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

#############################################################
#                      可自定义变量
#############################################################
DATA_DIR = "/media/shulab/Getea/zhe2/NC/sorted"  # AD01被试目录根路径
DO_ERODE = 1                # 是否执行腐蚀 (1=是,0=否)
MAX_JOBS = 20                # 最多同时执行多少个受试者任务 (过多可能内存不足)
# 下面这条需要你的环境中正确设置 $FSLDIR
REF_FA = os.path.join(os.environ.get('FSLDIR', ''), 'data', 'standard', 'FMRIB58_FA_1mm')
FNIRT_CONFIG = "FA_2_FMRIB58_1mm.cnf"  # FNIRT 配置文件 (需在FSL目录中或当前工作目录)
OUT_FA = "FA_in_MNI"       # 线性+非线性配准后输出(FA)
OUT_MD = "MD_in_MNI"       # 同理，对 MD 应用同样的warp
#############################################################


def run_cmd(cmd):
    print("[CMD]:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def delete_if_exists(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
        print(f"已删除文件: {file_path}")


def run_preproc_reg(subj_dir):
    subj_id = os.path.basename(subj_dir.rstrip("/"))
    # AD01的dti路径结构不同，改为dwi/dtifit
    dwi_dir = os.path.join(subj_dir, "dwi")
    dti_dir = os.path.join(dwi_dir, "dtifit")

    FA_IN = os.path.join(dti_dir, "dti_FA.nii.gz")
    MD_IN = os.path.join(dti_dir, "dti_MD.nii.gz")
    OUT_FA_FILE = os.path.join(dwi_dir, OUT_FA + ".nii.gz")
    OUT_MD_FILE = os.path.join(dwi_dir, OUT_MD + ".nii.gz")

    tmp_dir = os.path.join(dti_dir, "reg_temp")
    os.makedirs(tmp_dir, exist_ok=True)

    # 定义中间文件路径
    FA_ero = os.path.join(tmp_dir, "FA_ero.nii.gz")
    FA_mask = os.path.join(tmp_dir, "FA_ero_mask.nii.gz")
    fa2mni_affine = os.path.join(tmp_dir, "fa2mni_affine.mat")
    FA_lin = os.path.join(tmp_dir, "FA_lin.nii.gz")
    FA_to_MNI_warp = os.path.join(tmp_dir, "FA_to_MNI_warp.nii.gz")
    fnirt_log = os.path.join(tmp_dir, "fnirt.log")

    # 删除存在的结果文件和中间文件
    for file in [OUT_FA_FILE, OUT_MD_FILE, FA_ero, FA_mask, fa2mni_affine, FA_lin, FA_to_MNI_warp, fnirt_log]:
        delete_if_exists(file)

    print(f">>>> [开始] 处理被试 {subj_id}")

    if not os.path.isfile(FA_IN) or not os.path.isfile(MD_IN):
        print(f"!! 警告: {subj_id} 缺少 dti_FA 或 dti_MD, 跳过")
        return

    # (1) 腐蚀及裁剪
    if DO_ERODE == 1:
        print("  -> 腐蚀+裁剪")
        dimx = int(subprocess.check_output(["fslval", FA_IN, "dim1"]).decode().strip()) - 2
        dimy = int(subprocess.check_output(["fslval", FA_IN, "dim2"]).decode().strip()) - 2
        dimz = int(subprocess.check_output(["fslval", FA_IN, "dim3"]).decode().strip()) - 2

        run_cmd([
            "fslmaths", FA_IN,
            "-min", "1",
            "-ero",
            "-roi", "1", str(dimx), "1", str(dimy), "1", str(dimz), "0", "1",
            FA_ero
        ])

        run_cmd(["fslmaths", FA_ero, "-bin", FA_mask])

        FA_FOR_REG = FA_ero
        MASK_FOR_REG = FA_mask
    else:
        print("  -> 不执行腐蚀, 直接复制")
        run_cmd(["cp", FA_IN, FA_ero])

        run_cmd(["fslmaths", FA_ero, "-bin", FA_mask])

        FA_FOR_REG = FA_ero
        MASK_FOR_REG = FA_mask

    # (2) 线性 + 非线性配准
    print("  -> FLIRT")
    flirt_cmd = [
        "flirt",
        "-in", FA_FOR_REG,
        "-ref", REF_FA,
        "-omat", fa2mni_affine,
        "-out", FA_lin,
        "-interp", "trilinear",
        "-dof", "12"
    ]
    if MASK_FOR_REG:
        flirt_cmd.extend(["-inweight", MASK_FOR_REG])

    run_cmd(flirt_cmd)

    print("  -> FNIRT")
    fnirt_cmd = [
        "fnirt",
        f"--in={FA_FOR_REG}",
        f"--ref={REF_FA}",
        f"--aff={fa2mni_affine}",
        f"--cout={FA_to_MNI_warp}",
        f"--iout={OUT_FA_FILE}",
        f"--config={FNIRT_CONFIG}",
        f"--logout={fnirt_log}"
    ]
    run_cmd(fnirt_cmd)

    # (3) applywarp 到 MD
    MD_out = os.path.join(dwi_dir, OUT_MD + ".nii.gz")
    applywarp_cmd = [
        "applywarp",
        f"--in={MD_IN}",
        f"--ref={REF_FA}",
        f"--warp={FA_to_MNI_warp}",
        f"--out={MD_out}",
        "--abs",
        "--interp=trilinear"
    ]
    run_cmd(applywarp_cmd)

    print(f">>>> [完成] {subj_id}")


def main():
    print("并行腐蚀+配准脚本开始执行 ...")
    print(f"DATA_DIR = {DATA_DIR}")
    print(f"DO_ERODE = {DO_ERODE}")
    print(f"MAX_JOBS = {MAX_JOBS}")
    print()

    subfolders = [
        d for d in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, d))
    ]
    subfolders = [os.path.join(DATA_DIR, d) for d in subfolders]

    # AD01的验证路径改为dwi/dtifit
    valid_dirs = []
    for subj_dir in subfolders:
        dti_pre = os.path.join(subj_dir, "dwi", "dtifit")
        if not os.path.isdir(dti_pre):
            print(f"跳过 {subj_dir} (无 dwi/dtifit 子目录)")
        else:
            valid_dirs.append(subj_dir)

    with ThreadPoolExecutor(max_workers=MAX_JOBS) as executor:
        futures = []
        for sd in valid_dirs:
            futures.append(executor.submit(run_preproc_reg, sd))

        for future in as_completed(futures):
            future.result()

    print("所有受试者的并行腐蚀+配准处理完成！")


if __name__ == "__main__":
    main()
    
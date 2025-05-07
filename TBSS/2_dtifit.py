import os
import subprocess
from concurrent.futures import ThreadPoolExecutor


def run_dtifit(subject_dir):
    dwi_dir = os.path.join(subject_dir, 'dwi')
    output_dir = os.path.join(dwi_dir, 'dtifit')
    log_file = os.path.join(output_dir, 'dtifit.log')
    data = os.path.join(dwi_dir, 'data_ud.nii.gz')
    mask = os.path.join(dwi_dir, 'raw', 'b0_brain_mask.nii.gz')
    bvec_file = os.path.join(dwi_dir, 'bvecs')
    bval_file = os.path.join(dwi_dir, 'bvals')

    # 创建 dtifit 文件夹（如果不存在）
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created dtifit directory in {dwi_dir}")
        except OSError as e:
            print(f"Error creating dtifit directory in {dwi_dir}: {e}")
            return

    print(f"Running dtifit on {subject_dir}")
    command = [
        'dtifit',
        f'--data={data}',
        f'--out={output_dir}/dti',
        f'--mask={mask}',
        f'--bvecs={bvec_file}',
        f'--bvals={bval_file}',
        '--save_tensor'
    ]



def main(max_workers):
    base_dir = '/media/shulab/Getea/zhe2/NC/sorted/'
    subject_dirs = []
    for subject in os.listdir(base_dir):
        subject_dir = os.path.join(base_dir, subject)
        if os.path.isdir(subject_dir):
            subject_dirs.append(subject_dir)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(run_dtifit, subject_dirs)


if __name__ == "__main__":
    max_workers = 10  # 可根据需要修改最大线程数
    main(max_workers)
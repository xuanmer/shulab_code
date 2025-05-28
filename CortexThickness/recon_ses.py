from pathlib import Path
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed


def print_colored(msg, color_code):
    """Print message with the specified color."""
    print(f"\033[{color_code}m{msg}\033[0m")


def check_completion(ses_path):
    """Check if the recon-all process for a specific session is completed."""
    done_file = ses_path / 'fs' / 'scripts' / 'recon-all.done'
    log_file = ses_path / 'fs' / 'scripts' / 'recon-all.log'

    if done_file.exists():
        return True
    if log_file.exists():
        with open(log_file, 'r') as log:
            log_content = log.read()
            if "finished without error" in log_content:
                return True
    return False


def process_ses(ses_path):
    """Process the given session (ses-*)."""
    if not check_completion(ses_path):
        # 清理残留的fs文件夹
        fs_path = ses_path / 'fs'
        if fs_path.exists():
            shutil.rmtree(fs_path)
        
        # 构造包含通配符的命令字符串（关键修改）
        anat_dir = ses_path / 'anat'
        cmd = (
            f"recon-all -all "
            f"-i {anat_dir}/*.nii.gz "  # 通配符匹配anat目录下所有.nii.gz文件
            f"-sd {ses_path} -s fs"
        )

        try:
            print_colored(f"Starting recon-all for {ses_path}...", '32')
            print(f"执行命令: {cmd}")  # 打印完整命令便于调试
            # 启用shell=True以展开通配符
            subprocess.run(cmd, shell=True, check=True)
            print_colored(f"Recon-all finished for {ses_path}.", '32')
        except subprocess.CalledProcessError as e:
            print_colored(f"[ERROR] Recon-all failed for {ses_path}: {e}", '31')
            return ses_path


def main(base_path, max_threads=85):
    """Main function to process all incomplete sessions in parallel."""
    ses_items = []
    for sub_dir in Path(base_path).iterdir():
        if sub_dir.is_dir() and sub_dir.name.startswith('sub_'):  # 适配你的sub_命名
            for ses_dir in sub_dir.iterdir():
                if ses_dir.is_dir() and ses_dir.name.startswith('ses-'):
                    ses_items.append(ses_dir)
    ses_items.sort()

    incomplete_ses = [ses for ses in ses_items if not check_completion(ses)]

    if not incomplete_ses:
        print_colored("No incomplete recon-all processes found.", '33')
        return

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(process_ses, ses): ses for ses in incomplete_ses}
        for future in as_completed(futures):
            ses = futures[future]
            try:
                future.result()
            except Exception as e:
                print_colored(f"[ERROR] Failed processing {ses}: {e}", '31')

    print_colored('#######################\nDone\n##############################', '32')


# 示例运行（根据实际路径调整）
base_path = '/home/shulab/bty/ct_test/data'
main(base_path, 2)
    

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
        # 清理会话目录下的残留fs文件夹（如果存在）
        fs_path = ses_path / 'fs'
        if fs_path.exists():
            shutil.rmtree(fs_path)
        
        # 运行recon-all，输入为当前会话的anat数据，输出到会话目录下的fs
        try:
            print_colored(f"Starting recon-all for {ses_path}...", '32')
            cmd = [
                'recon-all', 
                '-all', 
                '-s', 'fs', 
                '-i', str(ses_path / 'anat' / 'data.nii.gz'),  # 会话级anat数据
                '-sd', str(ses_path)  # 输出根目录为当前会话目录
            ]
            print(' '.join(cmd))  # 打印命令便于调试
            subprocess.run(cmd, check=True)
            print_colored(f"Recon-all finished for {ses_path}.", '32')
        except subprocess.CalledProcessError as e:
            print_colored(f"[ERROR] Recon-all failed for {ses_path}: {e}", '31')
            return ses_path


def main(base_path, max_threads=85):
    """Main function to process all incomplete sessions in parallel."""
    ses_items = []
    for sub_dir in Path(base_path).iterdir():
        # 关键调整：匹配sub_开头的被试目录（原代码是startswith('sub-')）
        if sub_dir.is_dir() and sub_dir.name.startswith('sub_'):  
            for ses_dir in sub_dir.iterdir():
                if ses_dir.is_dir() and ses_dir.name.startswith('ses-'):  # 会话目录仍匹配ses-开头
                    ses_items.append(ses_dir)
    ses_items.sort()

    # 筛选未完成的会话
    incomplete_ses = [ses for ses in ses_items if not check_completion(ses)]

    if not incomplete_ses:
        print_colored("No incomplete recon-all processes found.", '33')
        return

    # 多线程并行处理会话
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
base_path = '/path/to/data'  # 指向你的data目录
main(base_path, 2)
    

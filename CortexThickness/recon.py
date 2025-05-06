#%%
from pathlib import Path
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed



def print_colored(msg, color_code):
    """Print message with the specified color."""
    print(f"\033[{color_code}m{msg}\033[0m")


def check_completion(path_item):
    """Check if the recon-all process is completed."""
    done_file = path_item / 'fs' / 'scripts' / 'recon-all.done'
    log_file = path_item / 'fs' / 'scripts' / 'recon-all.log'

    if done_file.exists():
        return True
    if log_file.exists():
        with open(log_file, 'r') as log:
            log_content = log.read()
            if "finished without error" in log_content:
                return True
    return False


def process_subject(path_item):
    """Process the given subject."""
    if not check_completion(path_item):
        # If the subject is incomplete, remove 'fs' folder and restart the process
        fs_path = path_item / 'fs'
        if fs_path.exists():
            shutil.rmtree(fs_path)
            
        """Run the recon-all command if not already completed."""
        try:
            print_colored(f"Starting recon-all for {path_item}...", '32')
            print(' '.join( ['recon-all', '-all', '-s', 'fs', '-i', str(path_item / 't1' / 'T1_unbiased.nii.gz'), '-sd', str(path_item)]))
            subprocess.run(
                ['recon-all', '-all', '-s', 'fs', '-i', str(path_item / 't1' / 'T1_unbiased.nii.gz'), '-sd', str(path_item)],
                check=True
            )
            print_colored(f"Recon-all finished for {path_item}.", '32')
        except subprocess.CalledProcessError as e:
            print_colored(f"[ERROR] Recon-all failed for {path_item}: {e}", '31')
            return path_item


def main(path_items, max_threads=85):
    """Main function to process all incomplete items in parallel."""
    # Prepare list of items
    items = [Path(path_items) / i for i in Path(path_items).iterdir() if (Path(path_items) / i).is_dir()]
    items.sort()
    incomplete_items = [item for item in items if not check_completion(item)]

    if not incomplete_items:
        print_colored("No incomplete recon-all processes found.", '33')

    # Use ThreadPoolExecutor for efficient multi-threading
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(process_subject, item): item for item in incomplete_items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                future.result()  # Block until this task is completed
            except Exception as e:
                print_colored(f"[ERROR] Failed processing {item}: {e}", '31')

    print_colored('#######################\nDone\n##############################', '32')


# Set the base path and start the processing
base_path = '/home/shulab/zhe2/NC/sorted'
main(base_path,78)

# %%

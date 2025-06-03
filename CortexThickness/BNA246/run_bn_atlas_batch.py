#!/usr/bin/env python3
"""
Batch run Brainnetome Atlas segmentation and statistics for multiple subjects in parallel.

Directory structure:
/tmp/
  ├── code/
  │     ├── run_bn_atlas_batch.py   # ← This batch script
  │     ├── BN_Atlas_246_LUT.txt
  │     ├── BN_Atlas_subcortex.gca
  │     ├── lh.BN_Atlas.gcs
  │     └── rh.BN_Atlas.gcs
  └── data/
        ├── 1000037/FreeSurfer/...
        ├── 1000463/FreeSurfer/...
        └── ...  (one folder per subject, each contains a FreeSurfer directory)

Usage:
    1. Place this script and all required atlas files under /tmp/code/
    2. Place each subject's FreeSurfer results under /tmp/data/SUBJECT_ID/FreeSurfer/
    3. Set MAX_THREADS to the desired level of parallelism (depends on your CPU cores)
    4. Run: python run_bn_atlas_batch.py
"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

# -------------------- Configurable parameters --------------------
MAX_THREADS = 4  # Maximum number of parallel threads (adjust as needed)

# Project root and atlas file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

LUT = os.path.join(CODE_DIR, "BN_Atlas_246_LUT.txt")
GCA = os.path.join(CODE_DIR, "BN_Atlas_subcortex.gca")
LH_GCS = os.path.join(CODE_DIR, "lh.BN_Atlas.gcs")
RH_GCS = os.path.join(CODE_DIR, "rh.BN_Atlas.gcs")

def process_subject(sub_id):
    """
    Run Brainnetome Atlas surface/volume parcellation and stats for a single subject.
    Each subject runs in a separate thread.
    """
    subj_dir = os.path.join(DATA_DIR, sub_id, "FreeSurfer")
    label_dir = os.path.join(subj_dir, "label")
    surf_dir = os.path.join(subj_dir, "surf")
    mri_dir = os.path.join(subj_dir, "mri")
    stats_dir = os.path.join(subj_dir, "stats")

    # 1. Surface parcellation (left & right hemisphere)
    cmd_lh = [
        "mris_ca_label", "-l", f"{label_dir}/lh.cortex.label",
        "FreeSurfer", "lh", f"{surf_dir}/lh.sphere.reg", LH_GCS, f"{label_dir}/lh.BN_Atlas.annot"
    ]
    cmd_rh = [
        "mris_ca_label", "-l", f"{label_dir}/rh.cortex.label",
        "FreeSurfer", "rh", f"{surf_dir}/rh.sphere.reg", RH_GCS, f"{label_dir}/rh.BN_Atlas.annot"
    ]
    # 2. Subcortical (volume) parcellation
    cmd_vol = [
        "mri_ca_label",
        f"{mri_dir}/brain.mgz", f"{mri_dir}/transforms/talairach.m3z",
        GCA, f"{mri_dir}/BN_Atlas_subcotex.mgz"
    ]
    # 3. Surface stats (left & right hemisphere)
    cmd_lh_stats = [
        "mris_anatomical_stats", "-mgz", "-cortex", f"{label_dir}/lh.cortex.label",
        "-f", f"{stats_dir}/lh.BN_Atlas.stats", "-b",
        "-a", f"{label_dir}/lh.BN_Atlas.annot", "-c", LUT, "FreeSurfer", "lh", "white"
    ]
    cmd_rh_stats = [
        "mris_anatomical_stats", "-mgz", "-cortex", f"{label_dir}/rh.cortex.label",
        "-f", f"{stats_dir}/rh.BN_Atlas.stats", "-b",
        "-a", f"{label_dir}/rh.BN_Atlas.annot", "-c", LUT, "FreeSurfer", "rh", "white"
    ]
    # 4. Volume stats (subcortical + subregions)
    cmd_vol_stats = [
        "mri_segstats",
        "--seg", f"{mri_dir}/BN_Atlas_subcotex.mgz",
        "--ctab", LUT, "--excludeid", "0",
        "--sum", f"{stats_dir}/BN_Atlas_subcotex.stats"
    ]

    # Set SUBJECTS_DIR for FreeSurfer commands
    env = os.environ.copy()
    env["SUBJECTS_DIR"] = os.path.join(DATA_DIR, sub_id)

    print(f"\n===== Processing subject: {sub_id} =====")
    try:
        subprocess.run(cmd_lh, env=env, check=True)
        subprocess.run(cmd_rh, env=env, check=True)
        subprocess.run(cmd_vol, env=env, check=True)
        subprocess.run(cmd_lh_stats, env=env, check=True)
        subprocess.run(cmd_rh_stats, env=env, check=True)
        subprocess.run(cmd_vol_stats, env=env, check=True)
        print(f"----- {sub_id} finished! -----")
    except subprocess.CalledProcessError as e:
        print(f"ERROR in {sub_id}: {e}")

if __name__ == "__main__":
    # Automatically detect all subject folders under data/
    all_subs = [
        name for name in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, name))
    ]
    print("Subjects detected:", all_subs)

    # Use a thread pool to process each subject in parallel
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(process_subject, all_subs)

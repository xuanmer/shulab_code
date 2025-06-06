#!/usr/bin/env python3
"""
Batch Parcellation and Statistics for Multiple Atlases using FreeSurfer

Author: bty
Date: 2025-06-06

Description:
    This script automates the batch processing of multiple subjects for 
    three surface-based brain atlases (BNA246, HCP-MMP1, Schaefer200) 
    using FreeSurfer. For each subject, both hemispheres are parcellated,
    and corresponding statistics are computed for both cortical and 
    subcortical regions. Results and logs are organized per subject.

Directory Structure Example:
tmp/
├── atlas/
│   ├── BN_Atlas_246/
│   │   ├── BN_Atlas_246_LUT.txt
│   │   ├── BN_Atlas_246_LUT_sub.txt
│   │   ├── BN_Atlas_subcortex.gca
│   │   ├── lh.BN_Atlas.gcs
│   │   └── rh.BN_Atlas.gcs
│   ├── HCP_MMP_1/
│   │   ├── lh.hcp-mmp-b_7p1.gcs
│   │   ├── rh.hcp-mmp-b_7p1.gcs
│   │   └── LUT_hcp-mmp-b.txt
│   └── Schaefer200/
│       ├── lh.Schaefer2018_200Parcels_17Networks.gcs
│       ├── rh.Schaefer2018_200Parcels_17Networks.gcs
│       └── Schaefer2018_200Parcels_17Networks_order_LUT.txt
├── code/
│   └── run_atlas_batch.py  # ← This script
└── data/
    ├── 1000037/
    │   └── FreeSurfer/
    │       ├── label/
    │       ├── surf/
    │       ├── mri/
    │       ├── stats/
    │       └── ...
    ├── 1000043/
    │   └── FreeSurfer/
    │       └── ...
    └── ... (more subjects)

Usage:
    1. Place this script under `tmp/code/`.
    2. Place all atlas files as shown above.
    3. Put each subject's FreeSurfer folder under `tmp/data/SUBJID/FreeSurfer/`.
    4. Set `MAX_THREADS` according to your CPU resources.
    5. Run: python run_atlas_batch.py
    6. Log file will be generated at `tmp/code/run_atlas_batch.log`.

"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ====== Configurations ======
MAX_THREADS = 4  # Adjust based on your CPU
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_PATH = os.path.join(CODE_DIR, "run_atlas_batch.log")

# ====== Atlas File Paths ======
# --- BNA246 ---
BNA246_DIR = os.path.join(PROJECT_ROOT, "atlas", "BN_Atlas_246")
BNA246_LUT = os.path.join(BNA246_DIR, "BN_Atlas_246_LUT.txt")
BNA246_LUT_SUB = os.path.join(BNA246_DIR, "BN_Atlas_246_LUT_sub.txt")
BNA246_GCA = os.path.join(BNA246_DIR, "BN_Atlas_subcortex.gca")
BNA246_LH_GCS = os.path.join(BNA246_DIR, "lh.BN_Atlas.gcs")
BNA246_RH_GCS = os.path.join(BNA246_DIR, "rh.BN_Atlas.gcs")

# --- HCP-MMP1 ---
HCP_MMP1_DIR = os.path.join(PROJECT_ROOT, "atlas", "HCP_MMP_1")
HCP_MMP1_LH_GCS = os.path.join(HCP_MMP1_DIR, "lh.hcp-mmp-b_7p1.gcs")
HCP_MMP1_RH_GCS = os.path.join(HCP_MMP1_DIR, "rh.hcp-mmp-b_7p1.gcs")
HCP_MMP1_LUT = os.path.join(HCP_MMP1_DIR, "LUT_hcp-mmp-b.txt")

# --- Schaefer200 ---
SCHAEFER200_DIR = os.path.join(PROJECT_ROOT, "atlas", "Schaefer200")
SCHAEFER200_LH_GCS = os.path.join(SCHAEFER200_DIR, "lh.Schaefer2018_200Parcels_17Networks.gcs")
SCHAEFER200_RH_GCS = os.path.join(SCHAEFER200_DIR, "rh.Schaefer2018_200Parcels_17Networks.gcs")
SCHAEFER200_LUT = os.path.join(SCHAEFER200_DIR, "Schaefer2018_200Parcels_17Networks_order_LUT.txt")


def write_log(msg):
    """
    Write a single log entry to the log file with timestamp.
    """
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")


def process_subject(sub_id):
    """
    Process one subject: Run all atlas parcellations and statistics.
    Outputs minimal progress to terminal, main status to log.
    """
    subj_dir = os.path.join(DATA_DIR, sub_id, "FreeSurfer")
    label_dir = os.path.join(subj_dir, "label")
    surf_dir = os.path.join(subj_dir, "surf")
    mri_dir = os.path.join(subj_dir, "mri")
    stats_dir = os.path.join(subj_dir, "stats")
    os.makedirs(label_dir, exist_ok=True)
    os.makedirs(stats_dir, exist_ok=True)

    # --- Prepare commands ---
    cmds = [
        # BNA246 (surface & subcortex)
        ["mris_ca_label", "-l", f"{label_dir}/lh.cortex.label", f"{sub_id}/FreeSurfer", "lh", f"{surf_dir}/lh.sphere.reg", BNA246_LH_GCS, f"{label_dir}/lh.BN_Atlas.annot"],
        ["mris_ca_label", "-l", f"{label_dir}/rh.cortex.label", f"{sub_id}/FreeSurfer", "rh", f"{surf_dir}/rh.sphere.reg", BNA246_RH_GCS, f"{label_dir}/rh.BN_Atlas.annot"],
        ["mri_ca_label", f"{mri_dir}/brain.mgz", f"{mri_dir}/transforms/talairach.m3z", BNA246_GCA, f"{mri_dir}/BN_Atlas_subcotex.mgz"],
        ["mris_anatomical_stats", "-mgz", "-cortex", f"{label_dir}/lh.cortex.label", "-f", f"{stats_dir}/lh.BN_Atlas.stats", "-b", "-a", f"{label_dir}/lh.BN_Atlas.annot", "-c", BNA246_LUT, f"{sub_id}/FreeSurfer", "lh", "white"],
        ["mris_anatomical_stats", "-mgz", "-cortex", f"{label_dir}/rh.cortex.label", "-f", f"{stats_dir}/rh.BN_Atlas.stats", "-b", "-a", f"{label_dir}/rh.BN_Atlas.annot", "-c", BNA246_LUT, f"{sub_id}/FreeSurfer", "rh", "white"],
        ["mri_segstats", "--seg", f"{mri_dir}/BN_Atlas_subcotex.mgz", "--ctab", BNA246_LUT_SUB, "--excludeid", "0", "--sum", f"{stats_dir}/BN_Atlas_subcotex.stats"],

        # HCP-MMP1 (surface)
        ["mris_ca_label", "-l", f"{label_dir}/lh.cortex.label", f"{sub_id}/FreeSurfer", "lh", f"{surf_dir}/lh.sphere.reg", HCP_MMP1_LH_GCS, f"{label_dir}/lh.hcp-mmp-b.annot"],
        ["mris_ca_label", "-l", f"{label_dir}/rh.cortex.label", f"{sub_id}/FreeSurfer", "rh", f"{surf_dir}/rh.sphere.reg", HCP_MMP1_RH_GCS, f"{label_dir}/rh.hcp-mmp-b.annot"],
        ["mris_anatomical_stats", "-a", f"{label_dir}/lh.hcp-mmp-b.annot", "-f", f"{stats_dir}/lh.hcp-mmp-b.stats", "-c", HCP_MMP1_LUT, f"{sub_id}/FreeSurfer", "lh"],
        ["mris_anatomical_stats", "-a", f"{label_dir}/rh.hcp-mmp-b.annot", "-f", f"{stats_dir}/rh.hcp-mmp-b.stats", "-c", HCP_MMP1_LUT, f"{sub_id}/FreeSurfer", "rh"],

        # Schaefer200 (surface)
        ["mris_ca_label", "-l", f"{label_dir}/lh.cortex.label", f"{sub_id}/FreeSurfer", "lh", f"{surf_dir}/lh.sphere.reg", SCHAEFER200_LH_GCS, f"{label_dir}/lh.Schaefer200.annot"],
        ["mris_ca_label", "-l", f"{label_dir}/rh.cortex.label", f"{sub_id}/FreeSurfer", "rh", f"{surf_dir}/rh.sphere.reg", SCHAEFER200_RH_GCS, f"{label_dir}/rh.Schaefer200.annot"],
        ["mris_anatomical_stats", "-a", f"{label_dir}/lh.Schaefer200.annot", "-f", f"{stats_dir}/lh.Schaefer200.stats", "-c", SCHAEFER200_LUT, f"{sub_id}/FreeSurfer", "lh"],
        ["mris_anatomical_stats", "-a", f"{label_dir}/rh.Schaefer200.annot", "-f", f"{stats_dir}/rh.Schaefer200.stats", "-c", SCHAEFER200_LUT, f"{sub_id}/FreeSurfer", "rh"],
    ]

    env = os.environ.copy()
    env["SUBJECTS_DIR"] = DATA_DIR

    write_log(f"[{sub_id}] ===== START processing =====")
    print(f"Processing {sub_id}...")  # Progress on terminal

    try:
        for cmd in cmds:
            subprocess.run(cmd, env=env, check=True)
        write_log(f"[{sub_id}] Finished.")
        print(f"{sub_id} finished.")
    except subprocess.CalledProcessError as e:
        write_log(f"[{sub_id}] ERROR: {e}")
        print(f"ERROR in {sub_id}: {e}")

if __name__ == "__main__":
    # Scan all subject folders (ignore 'fsaverage' etc.)
    all_subs = [
        name for name in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, name)) and name != "fsaverage"
    ]
    print("Subjects detected:", all_subs)

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(process_subject, all_subs)

    print("Batch finished. Check the log at", LOG_PATH)


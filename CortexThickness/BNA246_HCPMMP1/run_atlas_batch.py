#!/usr/bin/env python3
"""
Batch run Brainnetome Atlas (BNA246) and HCP-MMP1 parcellation and statistics for multiple subjects in parallel.
Directory structure:
tmp2/
  ├── code/
  │     ├── run_atlas_batch.py    # ← This script
  │     ├── BN_Atlas_246_LUT.txt
  │     ├── BN_Atlas_subcortex.gca
  │     ├── fsaverage/
  │     ├── lh.BN_Atlas.gcs
  │     ├── rh.BN_Atlas.gcs
  │     ├── lh.HCP-MMP1.annot
  │     ├── rh.HCP-MMP1.annot
  └── data/
        ├── 1000037/FreeSurfer/
        ├── 1000043/FreeSurfer/
        └── ... (subject folders)
"""
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

# -------------------- Configurable parameters --------------------
MAX_THREADS = 4  # Set this according to your CPU cores

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# -------------------- BNA246 atlas file paths --------------------
BNA246_LUT = os.path.join(CODE_DIR, "BN_Atlas_246_LUT.txt")
BNA246_LUT_SUB = os.path.join(CODE_DIR, "BN_Atlas_246_LUT_sub.txt")
BNA246_GCA = os.path.join(CODE_DIR, "BN_Atlas_subcortex.gca")
BNA246_LH_GCS = os.path.join(CODE_DIR, "lh.BN_Atlas.gcs")
BNA246_RH_GCS = os.path.join(CODE_DIR, "rh.BN_Atlas.gcs")

# -------------------- HCP-MMP1 atlas file paths --------------------
HCP_MMP1_LH_ANNOT = os.path.join(CODE_DIR, "lh.HCP-MMP1.annot")
HCP_MMP1_RH_ANNOT = os.path.join(CODE_DIR, "rh.HCP-MMP1.annot")

def process_subject(sub_id):
    """
    Run both BNA246 and HCP-MMP1 parcellation and stats for a single subject.
    """
    subj_dir = os.path.join(DATA_DIR, sub_id, "FreeSurfer")
    label_dir = os.path.join(subj_dir, "label")
    surf_dir = os.path.join(subj_dir, "surf")
    mri_dir = os.path.join(subj_dir, "mri")
    stats_dir = os.path.join(subj_dir, "stats")
    os.makedirs(label_dir, exist_ok=True)
    os.makedirs(stats_dir, exist_ok=True)

    # ========== BNA246 surface parcellation ==========
    cmd_bna246_lh = [
        "mris_ca_label", "-l", f"{label_dir}/lh.cortex.label",
        f"{sub_id}/FreeSurfer", "lh", f"{surf_dir}/lh.sphere.reg", BNA246_LH_GCS, f"{label_dir}/lh.BN_Atlas.annot"
    ]
    cmd_bna246_rh = [
        "mris_ca_label", "-l", f"{label_dir}/rh.cortex.label",
        f"{sub_id}/FreeSurfer", "rh", f"{surf_dir}/rh.sphere.reg", BNA246_RH_GCS, f"{label_dir}/rh.BN_Atlas.annot"
    ]
    # ========== BNA246 subcortical parcellation ==========
    cmd_bna246_vol = [
        "mri_ca_label",
        f"{mri_dir}/brain.mgz", f"{mri_dir}/transforms/talairach.m3z",
        BNA246_GCA, f"{mri_dir}/BN_Atlas_subcotex.mgz"
    ]
    # ========== BNA246 stats ==========
    cmd_bna246_lh_stats = [
        "mris_anatomical_stats", "-mgz", "-cortex", f"{label_dir}/lh.cortex.label",
        "-f", f"{stats_dir}/lh.BN_Atlas.stats", "-b",
        "-a", f"{label_dir}/lh.BN_Atlas.annot", "-c", BNA246_LUT, f"{sub_id}/FreeSurfer", "lh", "white"
    ]
    cmd_bna246_rh_stats = [
        "mris_anatomical_stats", "-mgz", "-cortex", f"{label_dir}/rh.cortex.label",
        "-f", f"{stats_dir}/rh.BN_Atlas.stats", "-b",
        "-a", f"{label_dir}/rh.BN_Atlas.annot", "-c", BNA246_LUT, f"{sub_id}/FreeSurfer", "rh", "white"
    ]
    cmd_bna246_vol_stats = [
        "mri_segstats",
        "--seg", f"{mri_dir}/BN_Atlas_subcotex.mgz",
        "--ctab", BNA246_LUT_SUB, "--excludeid", "0",
        "--sum", f"{stats_dir}/BN_Atlas_subcotex.stats"
    ]

    # ========== HCP-MMP1 surface parcellation ==========
    # NOTE: --srcsubject and --trgsubject are relative to SUBJECTS_DIR
    cmd_hcp_mmp1_lh = [
        "mri_surf2surf", "--srcsubject", "fsaverage", "--trgsubject", f"{sub_id}/FreeSurfer", "--hemi", "lh",
        "--sval-annot", HCP_MMP1_LH_ANNOT, "--tval", f"{label_dir}/lh.HCP-MMP1.annot"
    ]
    cmd_hcp_mmp1_rh = [
        "mri_surf2surf", "--srcsubject", "fsaverage", "--trgsubject", f"{sub_id}/FreeSurfer", "--hemi", "rh",
        "--sval-annot", HCP_MMP1_RH_ANNOT, "--tval", f"{label_dir}/rh.HCP-MMP1.annot"
    ]
    # HCP-MMP1 stats
    cmd_hcp_mmp1_lh_stats = [
        "mris_anatomical_stats", "-a", f"{label_dir}/lh.HCP-MMP1.annot",
        "-f", f"{stats_dir}/lh.HCP-MMP1.stats", f"{sub_id}/FreeSurfer", "lh"
    ]
    cmd_hcp_mmp1_rh_stats = [
        "mris_anatomical_stats", "-a", f"{label_dir}/rh.HCP-MMP1.annot",
        "-f", f"{stats_dir}/rh.HCP-MMP1.stats", f"{sub_id}/FreeSurfer", "rh"
    ]


    # Prepare env: SUBJECTS_DIR = data root, NOT each subject!
    env = os.environ.copy()
    env["SUBJECTS_DIR"] = DATA_DIR

    print(f"\n===== Processing subject: {sub_id} =====")
    try:
        # ------ BNA246 ------
        subprocess.run(cmd_bna246_lh, env=env, check=True)
        subprocess.run(cmd_bna246_rh, env=env, check=True)
        subprocess.run(cmd_bna246_vol, env=env, check=True)
        subprocess.run(cmd_bna246_lh_stats, env=env, check=True)
        subprocess.run(cmd_bna246_rh_stats, env=env, check=True)
        subprocess.run(cmd_bna246_vol_stats, env=env, check=True)
        # ------ HCP-MMP1 ------
        subprocess.run(cmd_hcp_mmp1_lh, env=env, check=True)
        subprocess.run(cmd_hcp_mmp1_rh, env=env, check=True)
        subprocess.run(cmd_hcp_mmp1_lh_stats, env=env, check=True)
        subprocess.run(cmd_hcp_mmp1_rh_stats, env=env, check=True)
        print(f"----- {sub_id} finished! -----")
    except subprocess.CalledProcessError as e:
        print(f"ERROR in {sub_id}: {e}")

if __name__ == "__main__":
    # Ensure fsaverage visible in data dir (only once)
    fsaverage_symlink = os.path.join(DATA_DIR, "fsaverage")
    fsaverage_source = os.path.join(CODE_DIR, "fsaverage")
    if not os.path.exists(fsaverage_symlink):
        os.symlink(fsaverage_source, fsaverage_symlink)

    # Scan all subject folders
    all_subs = [
        name for name in os.listdir(DATA_DIR)
        if os.path.isdir(os.path.join(DATA_DIR, name)) and name != "fsaverage"
    ]
    print("Subjects detected:", all_subs)

    # Run each subject in a thread
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(process_subject, all_subs)


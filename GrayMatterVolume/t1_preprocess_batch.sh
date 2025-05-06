#!/bin/bash

# ����߳������ɸ�����Ҫ������
MAX_THREADS=40
# ʹ�þ���·����ȡ��ǰ�ű�����Ŀ¼
SCRIPT_DIR=$(dirname "$(realpath "$0")")
# ����Ŀ¼�����б�����������Ŀ¼��
INPUT_DIR="/media/shulab/Getea/zhe2/NC/sorted"
# ���Ŀ¼���������·����
OUTPUT_DIR="/media/shulab/Getea/zhe2/NC/results"
# ͼ���ļ�·��������ʵ������޸ģ�
ATLAS="$SCRIPT_DIR/atlas/desikan-killiany_1mm.nii.gz"

# �������Ŀ¼
mkdir -p "$OUTPUT_DIR"

# ��ʼ���̼߳�����
THREAD_COUNT=0

# �������б����ļ��У��ų���ǰĿ¼����
find "$INPUT_DIR" -mindepth 1 -maxdepth 1 -type d -name '*' | while read -r subject_folder; do
    subject_id=$(basename "$subject_folder")
    echo "Processing subject: $subject_id"

    # ����������������
    cmd="$SCRIPT_DIR/t1_preprocess.sh '$subject_folder' '$OUTPUT_DIR/$subject_id' '$ATLAS'"
    echo "Executing command: $cmd"

    # ����Ԥ����ű�
    eval "$cmd" &

    ((THREAD_COUNT++))

    # ���Ʋ����߳���
    if [ "$THREAD_COUNT" -ge "$MAX_THREADS" ]; then
        wait -n
        ((THREAD_COUNT--))
    fi
done

# �ȴ������������
wait

echo "All subjects processed."
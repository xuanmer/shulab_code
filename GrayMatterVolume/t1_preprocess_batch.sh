input=$1
output=$2
atlas=$3

# input=/data/test_5
# output=/data/test_5_results

#for folder in `ls $input`
for folder in sub-1000043
do
  echo ${0%/*}
  ${0%/*}/t1_preprocess.sh $input/$folder $output/$folder $atlas
done
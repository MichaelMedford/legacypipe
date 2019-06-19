#!/bin/bash -l

# This script is run to process a single brick on a ZTF coadd


#export CODEPATH=/project/projectdirs/uLens/code/bin
export PROJECTPATH=/global/homes/c/cwar4677

#cd $PROJECTPATH/legacypipe/py
#source $PROJECTPATH/legacypipe/bin/legacypipe-env
#cd $PROJECTPATH



source $PROJECTPATH/legacypipe/bin/legacypipe-env

export LEGACY_SURVEY_DIR=/project/projectdirs/uLens/ZTF/Tractor/data/ZTF18aakxvxm/G_small/tractor

#export PYTHONPATH=/project/projectdirs/uLens/ZTF/Tractor/legacypipe/py:$PYTHONPATH
#export PYTHONPATH=/global/homes/c/cwar4677:$PYTHONPATH
export outdir=/global/homes/c/cwar4677/output_testing
export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH
export PYTHONPATH=$PROJECTPATH:$PYTHONPATH
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $outdir

python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --no-wise --stage coadds --brick=2395p525 --coadd-bw --nsigma=6 --threads=32 #--nblobs=100 --blob=1112 #--plots
#--stage fitblobs
#--threads=32
#--nblobs=1 --blob=1112 
#--blob=340
#--blob=274
#--radec=239.858822,52.209818
#--nblobs=50 --blob=750 --brick=2395p525 

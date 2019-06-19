#!/bin/bash -l

# This script is run to process a single brick on a ZTF coadd


#export CODEPATH=/project/projectdirs/uLens/code/bin
export PROJECTPATH=/global/homes/c/cwar4677

#cd $PROJECTPATH/legacypipe/py
#source $PROJECTPATH/legacypipe/bin/legacypipe-env
#cd $PROJECTPATH



source $PROJECTPATH/legacypipe/bin/legacypipe-env

export LEGACY_SURVEY_DIR=/global/homes/c/cwar4677/sims/sim30

#export PYTHONPATH=/project/projectdirs/uLens/ZTF/Tractor/legacypipe/py:$PYTHONPATH
#export PYTHONPATH=/global/homes/c/cwar4677:$PYTHONPATH
export outdir=$LEGACY_SURVEY_DIR #/global/homes/c/cwar4677/output_ZTF18aaymybb
export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH
export PYTHONPATH=$PROJECTPATH:$PYTHONPATH

#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker.py --folder=$LEGACY_SURVEY_DIR/images  
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR/images $outdir

python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --no-wise --coadd-bw --nsigma=20 --force-all --radec 239.4632622 52.44810708 --no-gaia -W 480 -H 480 --pixscale=1.012 --threads=32 --plots --no-splinesky #--threads=32 #--plots
#--stage fitblobs
#--radec 239.4632621952 52.44810708382
#--stage coadds
#--force-all
#--stage writecat
#-blobradec 288.656715 50.481882 
#--threads=32
#--nblobs=1 --blob=1112 
#--blob=340
#--blob=274
#--radec=239.858822,52.209818
#--nblobs=50 --blob=750 --brick=2395p525 

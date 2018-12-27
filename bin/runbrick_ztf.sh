#!/bin/bash -l

# This script is run to process a single brick on a ZTF coadd


export CODEPATH=/project/projectdirs/uLens/code/bin
export PROJECTPATH=/global/homes/c/cwar4677 
#export PROJECTPATH=/project/projectdirs/uLens/ZTF/Tractor/ #/global/homes/c/cwar4677

#cd $PROJECTPATH/legacypipe/py
#source $PROJECTPATH/legacypipe/bin/legacypipe-env
#cd $PROJECTPATH





export LEGACY_SURVEY_DIR=/project/projectdirs/uLens/ZTF/Tractor/data/ZTF18aakxvxm/G_small_v2/tractor

#export PYTHONPATH=/project/projectdirs/uLens/ZTF/Tractor/legacypipe/py:$PYTHONPATH
export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH
export PYTHONPATH=$PROJECTPATH:$PYTHONPATH

export outdir=/global/homes/c/cwar4677/output_individual
#rm $outdir/tractor*/*/*
#rm $outdir/coadd/*/*/*

#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker.py --folder=$LEGACY_SURVEY_DIR  
#rm $LEGACY_SURVEY_DIR/survey-ccds-ztf.fits
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $LEGACY_SURVEY_DIR
#rm -r $LEGACY_SURVEY_DIR/calib/
python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --no-wise --brick=2395p525  --coadd-bw --stage fit-blobs --blob 274 -nblobs=1
# --threads=32
#--radec=239.858822,52.209818
#--nblobs=100 --blob=750 --brick=2395p525 
#--stage fit-blobs

#!/bin/bash -l

# This script is run to process a single brick on a ZTF coadd

#export CODEPATH=/project/projectdirs/uLens/code/bin
export PROJECTPATH=/global/homes/c/cwar4677/tractor_dr8
source $PROJECTPATH/legacypipe/bin/legacypipe-env
#cd $PROJECTPATH/legacypipe/py
#source $PROJECTPATH/legacypipe/bin/legacypipe-env
#cd $PROJECTPATH

export LEGACY_SURVEY_DIR=/global/cscratch1/sd/cwar4677/ZTF18abcfdzu/tractor #/project/projectdirs/uLens/ZTF/Tractor/data/ZTF18abcfdzu/tractor

#export PYTHONPATH=/project/projectdirs/uLens/ZTF/Tractor/legacypipe/py:$PYTHONPATH
#export PYTHONPATH=/global/homes/c/cwar4677:$PYTHONPATH
export outdir=$LEGACY_SURVEY_DIR #/global/homes/c/cwar4677/output_ZTF18aaymybb
export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH
export PYTHONPATH=$PROJECTPATH/new_tractor/tractor-1:$PYTHONPATH

#python write_scielist_all.py
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker.py --folder=$LEGACY_SURVEY_DIR/images  
#python write_scielist.py 20180619000000
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $outdir

#python prep_forced.py ZTF18abcfdzu
#python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --coadd-bw --nsigma=5 --stage fitblobs --radec 230.217170 54.215558 --blobradec 230.217170 54.215558 --unwise-dir $LEGACY_SURVEY_DIR/images --no-wise --old-calibs-ok #--plots
#python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --pickle $outdir/pickles --coadd-bw --nsigma=5 --force-all --radec 230.217170 54.215558 --blobradec 230.217170 54.215558 --unwise-dir $LEGACY_SURVEY_DIR/images --no-wise --old-calibs-ok --threads=32 
#python write_scielist_all.py
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $outdir



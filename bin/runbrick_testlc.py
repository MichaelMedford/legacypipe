#!/bin/bash -l

# This script is run to process a single brick on a ZTF coadd

export PROJECTPATH=/global/homes/c/cwar4677/tractor_dr8

#cd $PROJECTPATH/legacypipe/py
source $PROJECTPATH/legacypipe/bin/legacypipe-env
#cd $PROJECTPATH


export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH
export PYTHONPATH=$PROJECTPATH/new_tractor/tractor-1:$PYTHONPATH


export LEGACY_SURVEY_DIR=/project/projectdirs/uLens/ZTF/Tractor/data/ZTF18aajytjt_PS1stack/tractor

#export PYTHONPATH=/project/projectdirs/uLens/ZTF/Tractor/legacypipe/py:$PYTHONPATH
#export PYTHONPATH=/global/homes/c/cwar4677:$PYTHONPATH
export outdir=$LEGACY_SURVEY_DIR #/global/homes/c/cwar4677/output_ZTF18aaymybb
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker_PS1.py --folder=$LEGACY_SURVEY_DIR/images  
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker_PS1.py $LEGACY_SURVEY_DIR $outdir
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker.py --folder=$LEGACY_SURVEY_DIR/images  
#python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $outdir


#python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --pickle $outdir/pickles --coadd-bw --nsigma=5 --stage writecat --radec 211.315074 +54.416022 --blobradec 211.315074 +54.416022 --unwise-dir $LEGACY_SURVEY_DIR/images --no-wise --old-calibs-ok --no-gaia

#python $PROJECTPATH/legacypipe/py/legacypipe/forced_photom.py --catalog $LEGACY_SURVEY_DIR/tractor-i/cus/tractor-custom-230217p54215.fits 53820533 CCD0  $LEGACY_SURVEY_DIR/tractor-i/cus/tractor-custom-230217p54215.fits testout 

#--stage fitblobs
#--stage writecat
#-blobradec 288.656715 50.481882 
#--threads=32
#--nblobs=1 --blob=1112 
#--blob=340
#--blob=274
#--radec=239.858822,52.209818
#--nblobs=50 --blob=750 --brick=2395p525 

#python $PROJECTPATH/legacypipe/py/legacypipe/forced_photom.py --no-ceres --no-move-gaia --catalog-dir=$LEGACY_SURVEY_DIR --catalog /project/projectdirs/uLens/ZTF/Tractor/data/ZTF18aajytjt_PS1stack/tractor/tractor-i/cus/tractor-custom-211315p54416.fits 78946684 CCD0  $LEGACY_SURVEY_DIR/tractor/cus/forced_78946684.fits

#python $PROJECTPATH/legacypipe/py/legacypipe/forced_photom.py --no-ceres --no-move-gaia --catalog-dir=$LEGACY_SURVEY_DIR --catalog /project/projectdirs/uLens/ZTF/Tractor/data/ZTF18aajytjt_PS1stack/tractor/tractor-i/cus/tractor-custom-211315p54416.fits 78946684 CCD0  $LEGACY_SURVEY_DIR/tractor/cus/forced_78946684.fits

python $PROJECTPATH/legacypipe/py/legacypipe/forced_photom.py --no-ceres --no-move-gaia --catalog-dir=$LEGACY_SURVEY_DIR --catalog /project/projectdirs/uLens/ZTF/Tractor/data/ZTF18aajytjt_PS1stack/tractor/tractor-i/cus/tractor-custom-211315p54416.fits 79347181 CCD0  $LEGACY_SURVEY_DIR/tractor/cus/forced_79347181.fits



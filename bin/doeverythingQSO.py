import numpy as np
import os
import glob
import subprocess
import sys
from astropy.io import fits
src=sys.argv[1]
ra=sys.argv[2]
dec=sys.argv[3]
datesplit=float(sys.argv[4])
band=sys.argv[5]
panstarrs=sys.argv[6]

directory='/global/cscratch1/sd/cwar4677/'+src+'_'+band+'/tractor'

file1='runbrick_'+src+'_'+band+'_ref.sh'

sciimgs=glob.glob(directory+'/images/ztf_20*'+band+'*sciimg.fits')
out=[]
datestart=datesplit#20180000000000

for img in sciimgs:
    try:
        x = float(img.split('/')[-1].split('_')[1])
    except ValueError:
        continue

    if x > datestart:
        out.append(img)
if len(out)>30:
    out=out[:10]

print(directory+'/scie.list')
np.savetxt(directory+'/scie.list',np.asarray(out,dtype=str),fmt='%s')
np.savetxt(directory+'/images/scie.list',np.asarray(out,dtype=str),fmt='%s')
if os.path.exists(file1):
    os.remove(file1)



with open(file1, 'a') as f:
    f.write('export PROJECTPATH=/global/homes/c/cwar4677/tractor_dr8\n')
    f.write('source $PROJECTPATH/legacypipe/bin/legacypipe-env\n')
    f.write('export LEGACY_SURVEY_DIR=/global/cscratch1/sd/cwar4677/'+src+'_'+band+'/tractor\n')
    f.write('export outdir=$LEGACY_SURVEY_DIR\n')
    f.write('export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH\n')
    f.write('export PYTHONPATH=$PROJECTPATH/new_tractor/tractor-1:$PYTHONPATH\n')
    f.write('python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker.py --folder=$LEGACY_SURVEY_DIR/images\n')
    f.write('python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $outdir\n')
    f.write('python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --pickle $outdir/pickles --coadd-bw --nsigma=5 --force-all --radec '+ra+' '+dec+' --blobradec '+ra+' '+dec+' --unwise-dir $LEGACY_SURVEY_DIR/images --no-wise --old-calibs-ok --threads=32')    

#command = 'cp /global/project/projectdirs/cosmo/data/legacysurvey/dr8/survey-ccds-decam-dr8.fits.gz '+directory
#subprocess.call(command,shell=True)

#Add code to actually run bash script?
#command='source '+file1
#subprocess.call(command,shell=True)


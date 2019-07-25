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

if panstarrs=='yes':
    #Generalized version of prep_PS1.py here...
    sciimgs=glob.glob(directory+'/images/*stk.g.unconv.fits')

    fn=sciimgs[0] 
    with open(fn,'rb') as f:
        hdul=fits.open(f)
        hdu = fits.PrimaryHDU(hdul[1].data)
        hdu.header=hdul[1].header
        hdu.header['EXTNAME']='CCD0'
        #print(hdul[1].header['BSOFTEN'])
        #BZERO   =   3.454127907753E+00
        #BSCALE  =   2.112995762387E-04
        BSOFTEN =   hdul[1].header['BSOFTEN'] #9.541472414983E+01
        BOFFSET =   hdul[1].header['BOFFSET'] #2.246295928955E+00

        v = hdul[1].data #BZERO + BSCALE * hdul[1].data
        a = 1.0857362
        x = v/a
        flux = BOFFSET + BSOFTEN * 2 * np.sinh(x)
        flux = np.nan_to_num(flux)
        hdu.data=flux

        print(hdul[1].header)
        hdu.writeto(fn.rstrip('.sciimg.fits')+'.new_sciimg.fits',overwrite=True)    

    fns=glob.glob(directory+'/images/*stk.g.unconv.mask.fits')
   
    for fn in fns:
        with open(fn,'rb') as f:
            hdul=fits.open(f)
            hdu = fits.PrimaryHDU(hdul[1].data, header=hdul[1].header)
            #hdu.header=hdul[1].header  
            hdu.header['EXTNAME']='CCD0'
            hdu.writeto(fn.rstrip('.mask.fits')+'.new_mskimg.fits',overwrite=True)
    
    fns=glob.glob(directory+'/images/*stk.g.unconv.wt.fits')

    for fn in fns:
        with open(fn,'rb') as f:
            hdul=fits.open(f)
            print(hdul[0].header)
            hdu = fits.PrimaryHDU(hdul[1].data, header=hdul[1].header)

            BSOFTEN =   hdul[1].header['BSOFTEN'] #9.541472414983E+01
            BOFFSET =   hdul[1].header['BOFFSET'] #2.246295928955E+00


            v = hdul[1].data #BZERO + BSCALE * hdul[1].data
            a = 1.0857362
            x = v/a
            flux = BOFFSET + BSOFTEN * 2 * np.sinh(x)
            #flux = np.nan_to_num(flux)
            hdu.data=flux


            #hdu.header=hdul[1].header  
            hdu.header['EXTNAME']='CCD0'
            hdu.writeto(fn.rstrip('.wt.fits')+'.weight.fits',overwrite=True)
    sciimgs=glob.glob(directory+'/images/*stk.g.unconv*new_sciimg*.fits')
    np.savetxt(directory+'/scie_PS1.list',np.asarray(sciimgs,dtype=str),fmt='%s')
    np.savetxt(directory+'/images/scie_PS1.list',np.asarray(sciimgs,dtype=str),fmt='%s')


sciimgs=glob.glob(directory+'/images/ztf_20*'+band+'*sciimg.fits')
out=[]
datestart=20180000000000
dateend=datesplit
for img in sciimgs:
    try:
        x = float(img.split('/')[-1].split('_')[1])
    except ValueError:
        continue

    if x > datestart and x < dateend:
        out.append(img)
if len(out)>30:
    out=out[:30]

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


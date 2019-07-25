from astropy.io import fits
import sys
import glob
import os
import gzip
#src='ZTF18aajytjt_PS1stack'
src=sys.argv[1]
directory='/global/cscratch1/sd/cwar4677/'+src+'/tractor'#os.getenv('LEGACY_SURVEY_DIR')
plotdir='/project/projectdirs/uLens/ZTF/Tractor/data/'+src+'/tractor/coadd/'
with gzip.open(directory+'/survey-ccds-ztf.fits.gz','rb') as f: 
    hdul=fits.open(f)
    
    expnums = hdul[1].data['EXPNUM']
    ccdsnames = hdul[1].data['CCDNAME']
print(len(expnums))

try:
    cat=glob.glob(directory+'/tractor-i/cus/tractor-custom*replace.fits')[0]
    print(cat)
except IndexError:
    cat=glob.glob(directory+'/tractor-i/cus/tractor-custom*.fits')[0]
for expnum,ccdname in zip(expnums[:100],ccdsnames[:100]):
    with open('runbrick_'+src+'.sh','a') as g:
        g.write('python $PROJECTPATH/legacypipe/py/legacypipe/forced_photom.py --no-ceres --no-move-gaia --catalog-dir=$LEGACY_SURVEY_DIR --catalog '+str(cat)+' ' +str(expnum)+' '+str(ccdname)+'  $LEGACY_SURVEY_DIR/tractor/cus/new2_forced_'+str(expnum)+'_'+str(ccdname)+'.fits\n\n')

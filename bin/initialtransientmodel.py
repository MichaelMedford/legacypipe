import subprocess
import sys
import numpy as np
import crossmatch as cm
import os
import glob
from astropy.time import Time
from astropy.io import fits
src=sys.argv[1]
ra=sys.argv[2]
dec=sys.argv[3]
datesplit=float(sys.argv[4])
src=sys.argv[5]
directory='/global/cscratch1/sd/cwar4677/'+src+'/tractor'
#if not os.path.exists(directory+'/backups'):
#        os.mkdir(directory+'/backups')
#command = 'mv '+directory+'/survey-ccds-decam-dr8.fits.gz '+directory+'/backups/'
#subprocess.call(command,shell=True)

file1='runbrick_'+src+'_ref.sh'

#Code to extract galaxy flux from catalog and put in new catalog

sciimgs=glob.glob(directory+'/images/ztf_20*sciimg.fits')
out=[]
datestart=datesplit
now=Time.now()
dateend=20200000000000
for img in sciimgs:
    if not os.path.exists(img.rstrip('sciimg.fits')+'mskimg.fits'):
        continue
    try:
        x = float(img.split('/')[-1].split('_')[1])
    except ValueError:
        continue

    if x > datestart and x < dateend:
        out.append(img)
if len(out)>100:
    out=out[-130:-30]

print(directory+'/scie.list')
np.savetxt(directory+'/scie.list',np.asarray(out,dtype=str),fmt='%s')
np.savetxt(directory+'/images/scie.list',np.asarray(out,dtype=str),fmt='%s')


cat=glob.glob(directory+'/tractor-i/cus/tractor-custom*.fits')[0]
fn=glob.glob(directory+'/metrics/cus/all-models-custom-*.fits')[0]
print('CHECK CAT FILES',cat,fn)
outdir=directory+'/metrics_gal/'
if not os.path.exists(outdir):
        os.mkdir(outdir)

srcra=float(ra)
srcdec=float(dec)

with fits.open(fn) as hdul:
	data=hdul[1].data
   
for i in range(data.shape[0]): 
    off=cm.precise_dist(srcra,srcdec,float(data[i]['psf_ra']),float(data[i]['psf_dec']))
    print(data[i]['psf_ra'],data[i]['psf_dec'],data[i]['type'])#,data[i]['dchisq'])
     
    if off*60*60<10.0:
        with open (outdir+'/'+str(i)+'_circle_'+src+'_psf.reg','w') as r:
            r.write('fk5;circle('+str(data[i]['psf_ra'])+','+str(data[i]['psf_dec'])+',0.2") # color = magenta\n')
        if data[0]['dchisq'][2]<data[0]['dchisq'][3]:
            with open (outdir+'/'+str(i)+'_circle_'+src+'_exp.reg','w') as r:
                r.write('fk5;circle('+str(data[i]['exp_ra'])+','+str(data[i]['exp_dec'])+',0.2") # color = magenta\n')
        else: 
            with open (outdir+'/'+str(i)+'_circle_'+src+'_dev.reg','w') as r:
                r.write('fk5;circle('+str(data[i]['dev_ra'])+','+str(data[i]['dev_dec'])+',0.2") # color = magenta\n')


command = 'mv '+cat+' '+cat.rstrip('.fits')+'-galaxymodel.fits'
print(command)
subprocess.call(command, shell=True)

command = 'mv '+fn+' '+fn.rstrip('.fits')+'-galaxymodel.fits'
print(command)
subprocess.call(command, shell=True)


if not os.path.exists(directory+'/coadd_gal'):
        os.mkdir(directory+'/coadd_gal')

command = 'mv '+directory+'/coadd/*/*/* '+directory+'/coadd_gal/'
print(command)
subprocess.call(command,shell=True)


if os.path.exists(file1):
    os.remove(file1)



with open(file1, 'a') as f:
    f.write('export PROJECTPATH=/global/homes/c/cwar4677/tractor_dr8\n')
    f.write('source $PROJECTPATH/legacypipe/bin/legacypipe-env\n')
    f.write('export LEGACY_SURVEY_DIR=/global/cscratch1/sd/cwar4677/'+src+'/tractor\n')
    f.write('export outdir=$LEGACY_SURVEY_DIR\n')
    f.write('export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH\n')
    f.write('export PYTHONPATH=$PROJECTPATH/new_tractor/tractor-1:$PYTHONPATH\n')
    f.write('python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker.py --folder=$LEGACY_SURVEY_DIR/images\n')
    f.write('python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $outdir\n')
    f.write('python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --pickle $outdir/pickles --coadd-bw --nsigma=5 --force-all --radec '+ra+' '+dec+' --blobradec '+ra+' '+dec+' --unwise-dir $LEGACY_SURVEY_DIR/images --no-wise --old-calibs-ok --transient --threads=32')    





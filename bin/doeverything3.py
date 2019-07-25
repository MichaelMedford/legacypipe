import gzip
import subprocess
import sys
import numpy as np
import os
import glob
from astropy.io import fits
import crossmatch as cm
src=sys.argv[1]
ra=sys.argv[2]
dec=sys.argv[3]
datesplit=float(sys.argv[4])
band=sys.argv[5]

directory='/global/cscratch1/sd/cwar4677/'+src+'_'+band+'/tractor'

file1='runbrick_'+src+'_'+band+'_ref.sh'
file2='runbrick_'+src+'_'+band+'forced.sh'

sciimgs=glob.glob(directory+'/images/ztf_20*sciimg.fits')
out=[]
datestart=datesplit
dateend=20200000000000

for img in sciimgs:
    try:
        x = float(img.split('/')[-1].split('_')[1])
    except ValueError:
        continue

    if x > datestart and x < dateend:
        out.append(img)

np.savetxt(directory+'/scie.list',np.asarray(out,dtype=str),fmt='%s')
np.savetxt(directory+'/images/scie.list',np.asarray(out,dtype=str),fmt='%s')
'''
with open(file2, 'a') as f:
    f.write('export PROJECTPATH=/global/homes/c/cwar4677/tractor_dr8\n')
    f.write('source $PROJECTPATH/legacypipe/bin/legacypipe-env\n')
    f.write('export LEGACY_SURVEY_DIR=/global/cscratch1/sd/cwar4677/'+src+'_'+band+'/tractor\n')
    f.write('export outdir=$LEGACY_SURVEY_DIR\n')
    f.write('export PYTHONPATH=$PROJECTPATH/legacypipe/py:$PYTHONPATH\n')
    f.write('export PYTHONPATH=$PROJECTPATH/new_tractor/tractor-1:$PYTHONPATH\n')
    f.write('python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfcoaddmaker.py --folder=$LEGACY_SURVEY_DIR/images\n')
    f.write('python $PROJECTPATH/legacypipe/py/ztfcoadd/ztfCCDtablemaker.py $LEGACY_SURVEY_DIR $outdir\n')
    #f.write('python $PROJECTPATH/legacypipe/py/legacypipe/runbrick.py --outdir=$outdir --pickle $outdir/pickles --coadd-bw --nsigma=5 --force-all --radec '+ra+' '+dec+' --blobradec '+ra+' '+dec+' --unwise-dir $LEGACY_SURVEY_DIR/images --no-wise --old-calibs-ok --threads=32')    


fn=glob.glob(directory+'/metrics/cus/all-models-custom-*.fits')
fn_gal=glob.glob(directory+'/metrics/cus/all-models-custom-*galaxymodel.fits')[0]
fn.remove(fn_gal)
fn=fn[0]

outdir=directory+'/metrics/'
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
        with open (outdir+'/'+str(i)+'_circle_'+src+'_psfdev.reg','w') as r:
            raerr=1/np.sqrt(float(data[i]['psfdev_ra_ivar']))*60*60
            decerr=1/np.sqrt(float(data[i]['psfdev_dec_ivar']))*60*60
            err1=10*np.abs(raerr*np.cos(float(data[i]['psfdev_dec'])))
            err2=10*decerr
            r.write('fk5;ellipse('+str(data[i]['psfdev_ra'])+','+str(data[i]['psfdev_dec'])+','+str(err1)+'",'+str(err2)+'") # color = magenta\n')
            raerr=1/np.sqrt(float(data[i]['psfdev_raPoint_ivar']))*60*60
            decerr=1/np.sqrt(float(data[i]['psfdev_decPoint_ivar']))*60*60
            err1=10*np.abs(raerr*np.cos(float(data[i]['psfdev_decPoint'])))
            err2=10*decerr
            r.write('fk5;ellipse('+str(data[i]['psfdev_raPoint'])+','+str(data[i]['psfdev_decPoint'])+','+str(err1)+'",'+str(err2)+'") # color = blue\n') 
        
        with open (outdir+'/'+str(i)+'_circle_'+src+'_psfexp.reg','w') as r:
            raerr=1/np.sqrt(float(data[i]['psfexp_ra_ivar']))*60*60
            decerr=1/np.sqrt(float(data[i]['psfexp_dec_ivar']))*60*60
            err1=10*np.abs(raerr*np.cos(float(data[i]['psfexp_dec'])))
            err2=10*decerr
            r.write('fk5;ellipse('+str(data[i]['psfexp_ra'])+','+str(data[i]['psfexp_dec'])+','+str(err1)+'",'+str(err2)+'") # color = magenta\n')
            raerr=1/np.sqrt(float(data[i]['psfexp_raPoint_ivar']))*60*60
            decerr=1/np.sqrt(float(data[i]['psfexp_decPoint_ivar']))*60*60
            err1=10*np.abs(raerr*np.cos(float(data[i]['psfexp_decPoint'])))
            err2=10*decerr
            r.write('fk5;ellipse('+str(data[i]['psfexp_raPoint'])+','+str(data[i]['psfexp_decPoint'])+','+str(err1)+'",'+str(err2)+'") # color = blue\n') 

cat=glob.glob(directory+'/tractor-i/cus/tractor-custom*.fits')
cat_gal=glob.glob(directory+'/tractor-i/cus/tractor-custom*-galaxymodel.fits')[0]
cat.remove(cat_gal)
cat=cat[0]

command = 'mv '+cat+' '+cat.rstrip('.fits')+'-transientmodel.fits'
print(command)
subprocess.call(command, shell=True)

command = 'mv '+fn+' '+fn.rstrip('.fits')+'-transientmodel.fits'
print(command)
subprocess.call(command, shell=True)


print(directory+'/metrics/cus/all-models-custom-*-galaxymodel.fits')

fn_gal=glob.glob(directory+'/metrics/cus/all-models-custom-*-galaxymodel.fits')[0]
with fits.open(fn_gal) as hdul:
    data_gal=hdul[1].data

def magToNanomaggies(mag):
    nmgy = 10. ** ((mag - 22.5) / -2.5)
    return nmgy

def nanomaggiesToMag(nmgy):
    mag = -2.5 * (np.log10(nmgy) - 9)
    return mag


catgal=glob.glob(directory+'/tractor-i/cus/tractor-custom*-galaxymodel.fits')[0]
cattransient=glob.glob(directory+'/tractor-i/cus/tractor-custom*-transientmodel.fits')[0]
with fits.open(cattransient) as f:       
    data=f[1].data
    header=f[1].header
    names=np.asarray([header[x] for x in header])
    for param_transient,param_gal in zip(['fluxGal'],['flux']):#,'ra','dec']:
        ind=np.argwhere(names==param_transient)[:,0][0]
        index_data=int(list(header.keys())[int(ind)].strip('TTYPE'))-1  
        if data[0]['dchisq'][2]<data[0]['dchisq'][3]: 
            data[0][index_data]=data_gal[0]['exp_'+param_gal]
        else:
            data[0][index_data]=data_gal[0]['dev_'+param_gal]
        
    fits.writeto(cat.rstrip('.fits')+'-replace.fits',data,header,overwrite=True) 
    print(cat.rstrip('.fits')+'-replace.fits')

'''


with gzip.open(directory+'/survey-ccds-ztf.fits.gz','rb') as f: 
    hdul=fits.open(f)    
    expnums = hdul[1].data['EXPNUM']
    ccdsnames = hdul[1].data['CCDNAME']
print('Number of data points is ',len(expnums))
cat = glob.glob(directory+'/tractor-i/cus/tractor-custom*replace.fits')[0]#cat.rstrip('.fits')+'-replace.fits'
taskname=directory+'/'+src+'_'+band+'_tasks.txt'
if os.path.exists(taskname):
    os.remove(taskname)

indices=np.arange(0,len(expnums),8)
for i in indices:
    maxind=min(len(expnums)-i,8)
   
    with open(file1) as f:
        wrapname=directory+'/wrap_'+src+str(i)+'.sh'
        if os.path.exists(wrapname):
            os.remove(wrapname)
        with open(wrapname,'a') as g:
            for x,line in enumerate(f):
                g.write(line)
                if x==5:
                    break
            for expnum,ccdname in zip(expnums[i:i+maxind],ccdsnames[i:i+maxind]):
                
                g.write('python $PROJECTPATH/legacypipe/py/legacypipe/forced_photom.py --no-ceres --no-move-gaia --catalog-dir=$LEGACY_SURVEY_DIR --catalog '+str(cat)+' ' +str(expnum)+' '+str(ccdname)+'  $LEGACY_SURVEY_DIR/tractor/cus/new2_forced_'+str(expnum)+'_'+str(ccdname)+'.fits\n\n')

        with open(taskname,'a') as h:
            h.write(directory+'/wrap_'+src+str(i)+'.sh\n')

command = 'chmod +x '+directory+'/wrap*'
subprocess.call(command,shell=True)

slfile='taskfarmer_'+src+'_'+band+'.sl'

if os.path.exists(slfile):
    os.remove(slfile)



with open(slfile,'a') as h:
    h.write('#!/bin/sh\n')
    h.write('#SBATCH -N 2 -c 64\n')
    h.write('#SBATCH -p debug\n')
    h.write('#SBATCH -t 00:30:00\n')
    h.write('#SBATCH -C haswell\n')
    h.write('cd '+directory+'\n')
    h.write('export PATH=$PATH:/usr/common/tig/taskfarmer/1.5/bin:$(pwd)\n')
    h.write('export THREADS=32\n')
    h.write('runcommands.sh '+src+'_'+band+'_tasks.txt\n')



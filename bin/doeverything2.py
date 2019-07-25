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
band=sys.argv[5]
directory='/global/cscratch1/sd/cwar4677/'+src+'_'+band+'/tractor'
#if not os.path.exists(directory+'/backups'):
#        os.mkdir(directory+'/backups')
#command = 'mv '+directory+'/survey-ccds-decam-dr8.fits.gz '+directory+'/backups/'
#subprocess.call(command,shell=True)

file1='runbrick_'+src+'_'+band+'ref.sh'
file2='runbrick_'+src+'_'+band+'sci.sh'
#Code to extract galaxy flux from catalog and put in new catalog

sciimgs=glob.glob(directory+'/images/ztf_20*sciimg.fits')
out=[]
datestart=datesplit
now=Time.now()
dateend=20200000000000
for img in sciimgs:
    try:
        x = float(img.split('/')[-1].split('_')[1])
    except ValueError:
        continue

    if x > datestart and x < dateend:
        out.append(img)
if len(out)>30:
    out=out[-50:-30]

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






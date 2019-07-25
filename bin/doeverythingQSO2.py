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
datestart=20180000000000
dateend=20200000000000
if len(out)>200:
    out=out[:200]
for img in sciimgs:
    try:
        x = float(img.split('/')[-1].split('_')[1])
    except ValueError:
        continue

    if x > datestart and x < dateend:
        out.append(img)
print(len(out))
np.savetxt(directory+'/scie.list',np.asarray(out,dtype=str),fmt='%s')
np.savetxt(directory+'/images/scie.list',np.asarray(out,dtype=str),fmt='%s')


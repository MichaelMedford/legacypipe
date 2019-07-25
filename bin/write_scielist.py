import glob
import os
import sys
import numpy as np
datestart=float(sys.argv[1])#20180200000000
dateend=float(sys.argv[2])
directory=os.getenv('LEGACY_SURVEY_DIR')

sciimgs=glob.glob(directory+'/images/ztf_20*sciimg.fits')
out=[]

for img in sciimgs:

    try:
        x = float(img.split('/')[-1].split('_')[1])
    except ValueError:
        continue

    if x > datestart and x < dateend:
        out.append(img)

print(directory+'/scie.list')
np.savetxt(directory+'/scie.list',np.asarray(out,dtype=str),fmt='%s')
np.savetxt(directory+'/images/scie.list',np.asarray(out,dtype=str),fmt='%s')

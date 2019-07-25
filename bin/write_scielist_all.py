import glob
import os
import sys
import numpy as np


directory=os.getenv('LEGACY_SURVEY_DIR')
sciimgs=glob.glob(directory+'/images/ztf_2018*sciimg.fits')+glob.glob(directory+'/images/ztf_2019*sciimg.fits')

np.savetxt(directory+'/scie.list',np.asarray(sciimgs,dtype=str),fmt='%s')
np.savetxt(directory+'/images/scie.list',np.asarray(sciimgs,dtype=str),fmt='%s')

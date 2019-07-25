import numpy as np
import os
import glob
import sys
from ztfquery import query
import subprocess
import time

zquery = query.ZTFQuery()
src=sys.argv[1]
ra=sys.argv[2]
dec=sys.argv[3]
datesplit=float(sys.argv[4])

zquery.load_metadata(kind='ref',radec=[ra,dec], size=0.001)
table=zquery.metatable[["field","filtercode", "ccdid","qid"]]

flag=0
for band in ['r','g']:
    directory='/global/cscratch1/sd/cwar4677/'+src+'/tractor'
    images=glob.glob(directory+'/images/'+band+'*sciimg.fits')
    print(directory,band,'nimages = ',len(images))
    out=[]
    for img in images:
        try:
            x = float(img.split('/')[-1].split('_')[1])
        except ValueError:
            continue
        if x < datesplit:
            out.append(img)

    if len(out)<10:
        flag=1

if flag==0:
    sys.exit()


for fieldid,fil,ccd,q in zip(table['field'],table['filtercode'],table['ccdid'],table['qid']):
    print(fieldid,fil,ccd,q)
    directory='/global/cscratch1/sd/cwar4677/'+src+'/tractor'

    if fil=='zi':
        continue
    if fil=='zg':
        fid='1'
    elif fil=='zr':
        fid='2' 
    if not os.path.exists(directory.strip('tractor')):
        os.mkdir(directory.strip('tractor'))
    if not os.path.exists(directory):
        os.mkdir(directory)
    if not os.path.exists(directory+'/images'):
        os.mkdir(directory+'/images')
   
    command = "python retrieve2.py 'FIELD="+str(fieldid)+" AND CCDID="+str(ccd)+" AND QID="+str(q)+" AND FID="+fid+" AND IPAC_GID=2'  --frame-destination="+directory+"/images"
    print(command) 
    subprocess.call(command,shell=True)
time.sleep(300) 

band_query=[]
for band in ['r','g']: 
    images=glob.glob(directory+'/images/*band*sciimg.fits')
    print(directory,band,'nimages = ',len(images))
    out=[]
    for img in images:
        try:
            x = float(img.split('/')[-1].split('_')[1])
        except ValueError:
            continue
        if x < datesplit:
            out.append(img)

    if len(out)<10:
        band_query.append(band)

print('Bands needing ztfquery: ',band_query)
for band in band_query:
    zquery.load_metadata(radec=[ra,dec], size=0.001, sql_query="seeing<3 AND filtercode='z"+band+"'",auth=['charlotteward@astro.umd.edu', 'p:uToigo'])
    zquery.download_data("sciimg.fits", show_progress=True)
    zquery.download_data("mskimg.fits", show_progress=True)
    command="mv ./Data/sci/*/*/*/*.fits "+directory+"/images/"
    print(command)
    if not os.path.exists(directory):
        os.mkdir(directory)
    subprocess.call(command,shell=True)

import subprocess
import os
import numpy as np
from ztfquery import marshal
import sys
src=sys.argv[1]
m = marshal.MarshalAccess()
m.load_target_sources(program="ZTFBH Offnuclear")

print(m.target_sources[m.target_sources['classification']==src])

directory='/global/cscratch1/sd/cwar4677'
taskname1=directory+'/'+src+'download_tasks.txt'
taskname2=directory+'/'+src+'model_tasks.txt'
if os.path.exists(taskname1):
    os.remove(taskname1)
if os.path.exists(taskname2):
    os.remove(taskname2)

file1=src+'downloads.sh'
file2=src+'jobs.sh'

if os.path.exists(file1):
    os.remove(file1)
if os.path.exists(file2):
    os.remove(file2)

source = m.target_sources#[m.target_sources['classification']==''+src+'']

with open(file1,'a') as f: 
    f.write('#!/bin/bash -l\n')
    f.write('cd /global/homes/c/cwar4677/tractor_dr8/legacypipe/bin\n')
    f.write('source activate imagedownload\n')

with open(file2,'a') as f: 
    f.write('#!/bin/bash -l\n')
    f.write('cd /global/homes/c/cwar4677/tractor_dr8/legacypipe/bin\n')
    f.write('source base_ZTF18abcfdzu.sh\n')
 
ind_src=np.argwhere(m.target_sources['classification']==src)[:,0]
print(ind_src)
indices=np.arange(0,20,5)#len(ind_src),20)
for i in indices:
    count=0
    maxind=min(len(ind_src)-i,5)
    wrapname=directory+'/wrap_'+src+str(i)+'download.sh'
    if os.path.exists(wrapname):
        os.remove(wrapname)
    with open(wrapname,'a') as g:
        g.write('#!/bin/bash -l\n')
        g.write('cd /global/homes/c/cwar4677/tractor_dr8/legacypipe/bin\n')
        g.write('source activate imagedownload\n') 
        for ind in ind_src[i:i+maxind]:
            if source['classification'][ind]!=src:
                continue
            g.write('python downloadimage_allband.py '+source['name'][ind]+' '+str(source['ra'][ind])+' '+str(source['dec'][ind])+' '+source['creationdate'][ind].replace('-','')+'000000 no\n')

    with open(taskname1,'a') as h:
        h.write(wrapname+'\n')
    wrapname=directory+'/wrap_'+src+str(i)+'model.sh'
    if os.path.exists(wrapname):
        os.remove(wrapname)

    with open(wrapname,'a') as g:
        g.write('#!/bin/bash -l\n')
        g.write('cd /global/homes/c/cwar4677/tractor_dr8/legacypipe/bin\n')
        g.write('source base_ZTF18abcfdzu.sh\n')
        for ind in ind_src[i:i+maxind]: 
            if source['classification'][ind]!=src:
                continue

            g.write('python initialgalmodel.py '+source['name'][ind]+' '+str(source['ra'][ind])+' '+str(source['dec'][ind])+' '+source['creationdate'][ind].replace('-','')+'000000 no '+src+'\n')
            g.write('source runbrick_'+source['name'][ind]+'_ref.sh\n')
            g.write('python initialtransientmodel.py '+source['name'][ind]+' '+str(source['ra'][ind])+' '+str(source['dec'][ind])+' '+source['creationdate'][ind].replace('-','')+'000000 no '+src+'\n')
            g.write('source runbrick_'+source['name'][ind]+'_ref.sh\n')
            g.write('python doforced.py '+source['name'][ind]+' '+str(source['ra'][ind])+' '+str(source['dec'][ind])+' '+source['creationdate'][ind].replace('-','')+'000000 no '+src+'\n')
            g.write('source runbrick_'+source['name'][ind]+'_forced.sh\n')

    with open(taskname2,'a') as h:
        h.write(wrapname+'\n')


command = 'chmod +x '+directory+'/wrap*'
subprocess.call(command,shell=True)

slfile='taskfarmer_'+src+'download.sl'

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
    h.write('runcommands.sh '+taskname1+'\n')

slfile='taskfarmer_'+src+'model.sl'

if os.path.exists(slfile):
    os.remove(slfile)



with open(slfile,'a') as h:
    h.write('#!/bin/sh\n')
    h.write('#SBATCH -N 2 -c 64\n')
    h.write('#SBATCH -p debug\n')
    h.write('#SBATCH -t 00:30:00\n')
    h.write('#SBATCH -C haswell\n')
    h.write('maxmem=134217728')
    h.write('ncores=8')
    h.write('let usemem=${maxmem}*${ncores}/64')
    h.write('ulimit -Sv $usemem')
    h.write('cd '+directory+'\n')
    h.write('export PATH=$PATH:/usr/common/tig/taskfarmer/1.5/bin:$(pwd)\n')
    h.write('export THREADS=8\n')
    h.write('runcommands.sh '+taskname2+'\n')





import os
import psycopg2
import pandas as pd
from argparse import ArgumentParser
from subprocess import check_call
import tempfile, io
import paramiko
from pathlib import Path


class HPSSDB(object):

    def __init__(self):

        dbname = 'ztfimages'
        password = 'WTU0p3ulJGPOerUP3C2q' 
        username = 'decam_admin' 
        port = '6666'
        host = 'private.caltech.edu' 
        dsn = f'host={host} user={username} dbname={dbname} password = {password} port={port}'

        self.connection = psycopg2.connect(dsn)
        self.cursor = self.connection.cursor()

    def __del__(self):

        del self.cursor
        del self.connection


def submit_hpss_job(tarfiles, images, job_script_destination, frame_destination, log_destination, tape_number):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    nersc_username = 'cwar4677'
    nersc_password = '@nellieGallifrey321'
    nersc_host = os.getenv('NERSC_HOST')
    nersc_account = 'ulens'

    ssh_client.connect(hostname=nersc_host, username=nersc_username, password=nersc_password)

    if job_script_destination is None:
        # then just use temporary files

        jobscript = tempfile.NamedTemporaryFile()
        subscript = tempfile.NamedTemporaryFile()

    else:

        jobscript = open(Path(job_script_destination) / f'hpss.{tape_number}.sh', 'w')
        subscript = open(Path(job_script_destination) / f'hpss.{tape_number}.sub.sh', 'w')

    subscript.write(f'''#!/usr/bin/env bash
module load esslurm
sbatch {Path(jobscript.name).resolve()}
    '''.encode('ASCII'))

    hpt = f'hpss.{tape_number}'

    jobstr = f'''#!/usr/bin/env bash
#SBATCH -J {tape_number}
#SBATCH -L SCRATCH,project
#SBATCH -q xfer
#SBATCH -N 1
#SBATCH -A {nersc_account}
#SBATCH -t 48:00:00
#SBATCH -C haswell
#SBATCH -o {(Path(log_destination) / hpt).resolve()}.out

cd {Path(frame_destination).resolve()}

'''



    for tarfile, imlist in zip(tarfiles, images):

        wildimages = '\n'.join([f'*{p}' for p in imlist])

        directive = f'''
/usr/common/mss/bin/hsi get {tarfile}
echo "{wildimages}" | tar --strip-components=12 -i --wildcards --wildcards-match-slash --files-from=- -xvf {os.path.basename(tarfile)}
rm {os.path.basename(tarfile)}

'''
        jobstr += directive

    jobscript.write(jobstr.encode('ASCII'))

    jobscript.seek(0)
    subscript.seek(0)


    stdin, stdout, stderr = ssh_client.exec_command(f'/bin/bash {Path(subscript.name).resolve()}')
    out = stdout.readlines()
    err = stderr.readlines()

    print(out, flush=True)
    print(err, flush=True)

    jobscript.close()
    subscript.close()
    

    jobid = int(out[0].strip().split()[-1])

    ssh_client.close()

    return jobid


def retrieve_images(whereclause, exclude_masks=False, job_script_destination=None, frame_destination='.', log_destination='.'):

    # interface to HPSS and database
    hpssdb = HPSSDB()

    # this is the query to get the image paths
    query = f'SELECT PATH, HPSS_SCI_PATH, HPSS_MASK_PATH FROM IMAGE WHERE HPSS_SCI_PATH IS NOT NULL ' \
            f'AND {whereclause}'
    hpssdb.cursor.execute(query)
    results = hpssdb.cursor.fetchall()

    df = pd.DataFrame(results, columns=['path', 'hpss_sci_path', 'hpss_mask_path'])

    dfsci = df[['path', 'hpss_sci_path']]
    dfsci = dfsci.rename({'hpss_sci_path': 'tarpath'}, axis='columns')

    if not exclude_masks:
        dfmask = df[['path', 'hpss_mask_path']].copy()
        dfmask.loc[:, 'path'] = [im.replace('sciimg', 'mskimg') for im in dfmask['path']]
        dfmask = dfmask.rename({'hpss_mask_path': 'tarpath'}, axis='columns')
        dfmask.dropna(inplace=True)
        df = pd.concat((dfsci, dfmask))
    else:
        df = dfsci

    tars = df['tarpath'].unique()

    # if nothing is found raise valueerror
    if len(tars) == 0:
        raise ValueError('No images match the given query')
    
    instr = '\n'.join(tars.tolist())

    with tempfile.NamedTemporaryFile() as f:
        f.write(f"{instr}\n".encode('ASCII'))

        # rewind the file
        f.seek(0)

        # sort tarball retrieval by location on tape
        sortexec = '/global/homes/c/cwar4677/hpss/hpsssort.sh'

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        nersc_username = 'cwar4677'#os.getenv('NERSC_USERNAME')
        nersc_password = '@nellieGallifrey321'#os.getenv('NERSC_PASSWORD')
        nersc_host = os.getenv('NERSC_HOST')

        ssh_client.connect(hostname=nersc_host, username=nersc_username, password=nersc_password)

        syscall = f'bash {sortexec} {f.name}'
        _, stdout, _ = ssh_client.exec_command(syscall)

        # read it into pandas
        ordered = pd.read_csv(stdout, delim_whitespace=True, names=['tape', 'position', '_', 'hpsspath'])

    # submit the jobs based on which tape the tar files reside on
    # and in what order they are on the tape

    dependency_dict = {}
    for tape, group in ordered.groupby('tape'):

        # get the tarfiles
        tarnames = group['hpsspath'].tolist()
        images = [df[df['tarpath'] == tarname]['path'].tolist() for tarname in tarnames]

        jobid = submit_hpss_job(tarnames, images, job_script_destination, frame_destination, log_destination, tape)
        for image in df['path']:
            dependency_dict[image] = jobid

    del hpssdb
    return dependency_dict


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("whereclause", default=None, type=str,
                        help='SQL where clause that tells the program which images to retrieve.')
    parser.add_argument('--exclude-masks', default=False, action='store_true',
                        help='Only retrieve the science images.')
    args = parser.parse_args()
    retrieve_images(args.whereclause, exclude_masks=args.exclude_masks)
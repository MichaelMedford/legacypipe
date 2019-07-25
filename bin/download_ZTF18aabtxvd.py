from ztfquery import query
from astropy.time import Time
import sys
zquery = query.ZTFQuery()

#jdobs=2458288.7074
#jdend=2458330.7020
#ra=230.217170 
#dec=+54.215558
#jdobs=2458272.7589
#jdend=2458307.7144
#ra=249.262968
#dec=+44.091763
#jdobs=2458422.8865
#jdend=2458450.9497
#ra=105.935177
#dec=+59.544834
jdobs=2200000
jdend=2458132.9153
#jdend=2458609.6802
ra=119.227287
dec=+34.262119

zquery.load_metadata(kind='ref',radec=[ra,dec], size=0.001, sql_query="filtercode='zg'")
print(zquery.metatable[["startobsdate","endobsdate","field","filtercode", "ccdid","qid","nframes"]])
zquery.download_data("refimg.fits", show_progress=False)
zquery.load_metadata(kind='ref',radec=[ra,dec], size=0.001, sql_query="filtercode='zr'")
print(zquery.metatable[["startobsdate","endobsdate","field","filtercode", "ccdid","qid","nframes"]])
zquery.download_data("refimg.fits", show_progress=False)

sys.exit()


refstart=Time(['2018-02-17T05:52:37'],format='isot')
refend=Time(['2018-11-05T10:16:14.083'],format='isot')
jdend=refstart.jd[0]-55.9
print(refstart.jd,refend.jd,Time(jdend,format='jd').isot)


#zquery.load_metadata(kind='ref',radec=[ra,dec], size=0.001, sql_query="filtercode='zg'")
#zquery.download_data("mskimg.fits")


zquery.load_metadata(radec=[ra,dec], size=0.001, sql_query="seeing<3 and obsjd BETWEEN "+str(jdobs)+' AND '+str(jdend)+" AND filtercode='zg'",auth=['charlotteward@astro.umd.edu', 'nellie42'])
print(zquery.metatable[["obsdate","obsjd", "seeing", "filtercode"]])


zquery.download_data("sciimg.fits", show_progress=False)
zquery.download_data("mskimg.fits", show_progress=False)

#rm /Users/charlotteward/phd/ztfdatasci/*/*/*/*.fits
#cp /Users/charlotteward/phd/ztfdatasci/*/*/*/*.fits /project/projectdirs/uLens/ZTF/Tractor/data/ZTF18abcfdzu/tractor/images



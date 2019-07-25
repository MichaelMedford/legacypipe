import matplotlib as mpl
mpl.use('Agg')
from astropy.io import fits
import sys
import glob
import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time
src=sys.argv[1]
band=sys.argv[2]
basedir='/global/cscratch1/sd/cwar4677/'+src+'_'+band+'/tractor/tractor/cus'


def nanomaggiesToMag(nmgy):
    mag = -2.5 * (np.log10(nmgy) - 9)
    return mag

def fluxErrorsToMagErrors(flux, flux_invvar):
    flux = np.atleast_1d(flux)
    flux_invvar = np.atleast_1d(flux_invvar)
    dflux = np.zeros(len(flux))
    okiv = (flux_invvar > 0)
    dflux[okiv] = (1. / np.sqrt(flux_invvar[okiv]))
    okflux = (flux > 0)
    mag = np.zeros(len(flux))
    mag[okflux] = (nanomaggiesToMag(flux[okflux]))
    dmag = np.zeros(len(flux))
    ok = (okiv * okflux)
    dmag[ok] = (np.abs((-2.5 / np.log(10.)) * dflux[ok] / flux[ok]))
    mag[np.logical_not(okflux)] = np.nan
    dmag[np.logical_not(ok)] = np.nan
    return mag.astype(np.float32), dmag.astype(np.float32)



cat=glob.glob(basedir+'/tractor-custom*.fits')[0]
allforced=glob.glob(basedir+'/new2_forced*.fits')
print(len(allforced),'datapoints')

datag=[]
datar=[]
print(len(allforced))
for forced in allforced:
    with open(forced,'rb') as f:
        hdul=fits.open(f) 
       
        if hdul[1].data[0][10]==band:
            datag.append([hdul[1].data[0][11],hdul[1].data[0][0],hdul[1].data[0][1],hdul[1].data[0][2]])
        else:
            datar.append([hdul[1].data[0][11],hdul[1].data[0][0],hdul[1].data[0][1],hdul[1].data[0][2]])
       

datag=np.asfarray(datag)
now=Time.now()

sorteddatag=datag[datag[:,0].argsort()]
err=1/np.sqrt(sorteddatag[:,2])
#print(err,err/sorteddatag[:,1])
#plt.plot(sorteddatag[:,0],sorteddatag[:,1]+sorteddatag[:,2],label='total flux')
plt.errorbar(sorteddatag[:,0]-now.mjd,sorteddatag[:,1],yerr=np.multiply(err,1),label='Band = '+band,marker='.',linestyle='')
plt.plot(sorteddatag[:,0]-now.mjd,sorteddatag[:,2],label='fluxGal')
plt.legend()
#plt.gca().invert_yaxis()
plt.xlabel('Days ago')
#plt.ylim((21,18))
plt.ylabel('flux (nanomaggies)')
plt.savefig(basedir+'/'+src+'_'+band+'_lc.png')
def mag(x):
    return 22.5-2.5*np.log10(x)
plt.clf()

mags,magerr=fluxErrorsToMagErrors(sorteddatag[:,1],err/2.)
maggal,magerr=fluxErrorsToMagErrors(sorteddatag[:,2],err/2.)
print(maggal)


#plt.scatter(sorteddatag[:,0]-now.jd,mag(sorteddatag[:,1]+sorteddatag[:,2]),label='total flux',marker='.')
print(sorteddatag[:,0])
plt.errorbar(sorteddatag[:,0]-now.mjd,mags,yerr=magerr,label='fluxPoint',marker='.',linestyle='')
plt.scatter(sorteddatag[:,0]-now.mjd,maggal,label='fluxGal',marker='.',s=1,linestyle='-',color='orange')
print(np.max(mags[~np.isnan(mags)]),np.max(maggal[~np.isnan(maggal)]))
print(np.min(mags[~np.isnan(mags)])-0.5)
#plt.ylim((np.max([np.max(mags[~np.isnan(mags)]),np.max(maggal[~np.isnan(maggal)])])+0.5,np.min(mags[~np.isnan(mags)])-0.5))
plt.ylim((20,17.9))
plt.legend()
plt.xlabel('Days Ago')
plt.ylabel('Magnitude')
plt.savefig(basedir+'/'+src+'_'+band+'_lcmag.png')
print('Saved', basedir+'/'+src+'_'+band+'_lcmag.png')
mags,magerr=fluxErrorsToMagErrors(sorteddatag[:,1]+sorteddatag[:,2],err)
plt.clf()
plt.errorbar(sorteddatag[:,0]-now.mjd,mags,yerr=magerr,label='band = '+band,marker='.',linestyle='')
'''
if band =='r':

    plt.ylim((16.25,15.3))
else:
    plt.ylim((17,15.3))
'''

plt.ylim((np.max(mags[~np.isnan(mags)])+0.1,np.min(mags[~np.isnan(mags)])-0.1))


plt.legend()
plt.xlabel('Days Ago')
plt.ylabel('Magnitude')
plt.savefig(basedir+'/'+src+'_'+band+'_lctotalmag.png')
plt.clf()


from astropy.io import fits
import numpy as np
import glob
directory='/global/cscratch1/sd/cwar4677/ZTF18abcfdzu/tractor'
gmag=20.53

cat=glob.glob(directory+'/tractor-i/cus/tractor-custom*.fits')[0]
print(cat)

def magToNanomaggies(mag):
    nmgy = 10. ** ((mag - 22.5) / -2.5)
    return nmgy

def nanomaggiesToMag(nmgy):
    mag = -2.5 * (np.log10(nmgy) - 9)
    return mag


with fits.open(cat) as f:       
    data=f[1].data
    header=f[1].header
    names=np.asarray([header[x] for x in header])
    ind=np.argwhere(names=='fluxGal')[:,0][0]
    index_data=int(list(header.keys())[int(ind)].strip('TTYPE'))-1 
    
    print('tractor fit', nanomaggiesToMag(data[0][index_data]))
    fluxes=magToNanomaggies(gmag)
    print(fluxes) 
    data[0][index_data]=fluxes
    
    fits.writeto(cat.rstrip('.fits')+'-replace.fits',data,header,overwrite=True) 
    print(cat.rstrip('.fits')+'-replace.fits')

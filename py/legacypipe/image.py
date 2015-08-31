from __future__ import print_function
import os
import numpy as np
import fitsio
from tractor.utils import get_class_from_name
from tractor.basics import NanoMaggies, ConstantFitsWcs, LinearPhotoCal
from tractor.image import Image
from .common import CP_DQ_BITS

class LegacySurveyImage(object):
    '''
    A base class containing common code for the images we handle.

    You shouldn't directly instantiate this class, but rather use the appropriate
    subclass:
     * DecamImage
     * BokImage
    '''

    def __init__(self, decals, ccd):
        '''

        Create a new LegacySurveyImage object, from a Decals object,
        and one row of a CCDs fits_table object.

        You may not need to instantiate this class directly, instead using
        Decals.get_image_object():

            decals = Decals()
            # targetwcs = ....
            # ccds = decals.ccds_touching_wcs(targetwcs, ccdrad=None)
            ccds = decals.get_ccds()
            im = decals.get_image_object(ccds[0])
            # which does the same thing as:
            im = DecamImage(decals, ccds[0])

        Or, if you have a Community Pipeline-processed input file and
        FITS HDU extension number:

            decals = Decals()
            ccds = exposure_metadata([filename], hdus=[hdu])
            im = DecamImage(decals, ccds[0])

        Perhaps the most important method in this class is
        *get_tractor_image*.

        '''
        self.decals = decals

        imgfn, hdu, band, expnum, ccdname, exptime = (
            ccd.image_filename.strip(), ccd.image_hdu, ccd.filter.strip(), 
            ccd.expnum, ccd.ccdname.strip(), ccd.exptime)

        if os.path.exists(imgfn):
            self.imgfn = imgfn
        else:
            self.imgfn = os.path.join(self.decals.get_image_dir(), imgfn)

        self.hdu   = hdu
        self.expnum = expnum
        self.ccdname = ccdname.strip()
        self.band  = band
        self.exptime = exptime
        self.camera = ccd.camera.strip()
        self.fwhm = ccd.fwhm
        # in arcsec/pixel
        self.pixscale = 3600. * np.sqrt(np.abs(ccd.cd1_1 * ccd.cd2_2 - ccd.cd1_2 * ccd.cd2_1))

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def get_good_image_slice(self, extent, get_extent=False):
        '''
        extent = None or extent = [x0,x1,y0,y1]

        If *get_extent* = True, returns the new [x0,x1,y0,y1] extent.

        Returns a new pair of slices, or *extent* if the whole image is good.
        '''
        gx0,gx1,gy0,gy1 = self.get_good_image_subregion()
        if gx0 is None and gx1 is None and gy0 is None and gy1 is None:
            return extent
        if extent is None:
            imh,imw = self.get_image_shape()
            extent = (0, imw, 0, imh)
        x0,x1,y0,y1 = extent
        if gx0 is not None:
            x0 = max(x0, gx0)
        if gy0 is not None:
            y0 = max(y0, gy0)
        if gx1 is not None:
            x1 = min(x1, gx1)
        if gy1 is not None:
            y1 = min(y1, gy1)
        if get_extent:
            return (x0,x1,y0,y1)
        return slice(y0,y1), slice(x0,x1)

    def get_good_image_subregion(self):
        '''
        Returns x0,x1,y0,y1 of the good region of this chip,
        or None if no cut should be applied to that edge; returns
        (None,None,None,None) if the whole chip is good.

        This cut is applied in addition to any masking in the mask or
        invvar map.
        '''
        return None,None,None,None

    def get_tractor_image(self, slc=None, radecpoly=None,
                          gaussPsf=False, const2psf=False, pixPsf=False,
                          nanomaggies=True, subsky=True, tiny=5):
        '''
        Returns a tractor.Image ("tim") object for this image.
        
        Options describing a subimage to return:

        - *slc*: y,x slice objects
        - *radecpoly*: numpy array, shape (N,2), RA,Dec polygon describing bounding box to select.

        Options determining the PSF model to use:

        - *gaussPsf*: single circular Gaussian PSF based on header FWHM value.
        - *const2Psf*: 2-component general Gaussian fit to PsfEx model at image center.
        - *pixPsf*: pixelized PsfEx model at image center.

        Options determining the units of the image:

        - *nanomaggies*: convert the image to be in units of NanoMaggies;
          *tim.zpscale* contains the scale value the image was divided by.

        - *subsky*: subtract a constant sky value, leaving pixel
           values distributed around zero.  *tim.midsky* contains the
           value subtracted.

        '''
        from astrometry.util.miscutils import clip_polygon
        
        band = self.band
        imh,imw = self.get_image_shape()

        wcs = self.get_wcs()
        x0,y0 = 0,0
        x1 = x0 + imw
        y1 = y0 + imh
        if slc is None and radecpoly is not None:
            imgpoly = [(1,1),(1,imh),(imw,imh),(imw,1)]
            ok,tx,ty = wcs.radec2pixelxy(radecpoly[:-1,0], radecpoly[:-1,1])
            tpoly = zip(tx,ty)
            clip = clip_polygon(imgpoly, tpoly)
            clip = np.array(clip)
            if len(clip) == 0:
                return None
            x0,y0 = np.floor(clip.min(axis=0)).astype(int)
            x1,y1 = np.ceil (clip.max(axis=0)).astype(int)
            slc = slice(y0,y1+1), slice(x0,x1+1)
            if y1 - y0 < tiny or x1 - x0 < tiny:
                print('Skipping tiny subimage')
                return None
        if slc is not None:
            sy,sx = slc
            y0,y1 = sy.start, sy.stop
            x0,x1 = sx.start, sx.stop

        old_extent = (x0,x1,y0,y1)
        new_extent = self.get_good_image_slice((x0,x1,y0,y1), get_extent=True)
        if new_extent != old_extent:
            x0,x1,y0,y1 = new_extent
            print('Applying good subregion of CCD: slice is', x0,x1,y0,y1)
            if x0 >= x1 or y0 >= y1:
                return None
            slc = slice(y0,y1), slice(x0,x1)

        print('Reading image slice:', slc)
        img,imghdr = self.read_image(header=True, slice=slc)

        # check consistency... something of a DR1 hangover
        e = imghdr['EXTNAME']
        assert(e.strip() == self.ccdname.strip())

        invvar = self.read_invvar(slice=slc)
        dq = self.read_dq(slice=slc)
        invvar[dq != 0] = 0.
        if np.all(invvar == 0.):
            print('Skipping zero-invvar image')
            return None
        assert(np.all(np.isfinite(img)))
        assert(np.all(np.isfinite(invvar)))
        assert(not(np.all(invvar == 0.)))

        # header 'FWHM' is in pixels
        # imghdr['FWHM']
        psf_fwhm = self.fwhm 
        psf_sigma = psf_fwhm / 2.35
        primhdr = self.read_image_primary_header()

        sky = self.read_sky_model()
        midsky = sky.getConstant()
        if subsky:
            img -= midsky
            sky.subtract(midsky)

        magzp = self.decals.get_zeropoint_for(self)
        orig_zpscale = zpscale = NanoMaggies.zeropointToScale(magzp)
        if nanomaggies:
            # Scale images to Nanomaggies
            img /= zpscale
            invvar *= zpscale**2
            zpscale = 1.

        assert(np.sum(invvar > 0) > 0)
        sig1 = 1./np.sqrt(np.median(invvar[invvar > 0]))
        assert(np.all(np.isfinite(img)))
        assert(np.all(np.isfinite(invvar)))
        assert(np.isfinite(sig1))

        twcs = ConstantFitsWcs(wcs)
        if x0 or y0:
            twcs.setX0Y0(x0,y0)

        psffn = None
        if gaussPsf:
            #from tractor.basics import NCircularGaussianPSF
            #psf = NCircularGaussianPSF([psf_sigma], [1.0])
            from tractor.basics import GaussianMixturePSF
            v = psf_sigma**2
            psf = GaussianMixturePSF(1., 0., 0., v, v, 0.)
            print('WARNING: using mock PSF:', psf)
            psf.version = '0'
            psf.plver = ''
        elif pixPsf:
            # spatially varying pixelized PsfEx
            from tractor.psfex import PixelizedPsfEx
            print('Reading PsfEx model from', self.psffn)
            psf = PixelizedPsfEx(self.psffn)
            psf.shift(x0, y0)
            psffn = self.psffn

        elif const2psf:
            from tractor.psfex import PsfExModel
            from tractor.basics import GaussianMixtureEllipsePSF
            # 2-component constant MoG.
            print('Reading PsfEx model from', self.psffn)
            psffn = self.psffn
            psfex = PsfExModel(self.psffn)
            psfim = psfex.at(imw/2., imh/2.)
            psfim = psfim[5:-5, 5:-5]
            print('Fitting PsfEx model as 2-component Gaussian...')
            psf = GaussianMixtureEllipsePSF.fromStamp(psfim, N=2)
            del psfim
            del psfex
        else:
            assert(False)
        print('Using PSF model', psf)

        if psffn is not None:
            hdr = fitsio.read_header(psffn)
            psf.version = hdr.get('LEGSURV', None)
            if psf.version is None:
                psf.version = str(os.stat(psffn).st_mtime)
            psf.plver = hdr.get('PLVER', '').strip()

        tim = Image(img, invvar=invvar, wcs=twcs, psf=psf,
                    photocal=LinearPhotoCal(zpscale, band=band),
                    sky=sky, name=self.name + ' ' + band)
        assert(np.all(np.isfinite(tim.getInvError())))
        tim.zr = [-3. * sig1, 10. * sig1]
        tim.zpscale = orig_zpscale
        tim.midsky = midsky
        tim.sig1 = sig1
        tim.band = band
        tim.psf_fwhm = psf_fwhm
        tim.psf_sigma = psf_sigma
        tim.sip_wcs = wcs
        tim.x0,tim.y0 = int(x0),int(y0)
        tim.imobj = self
        tim.primhdr = primhdr
        tim.hdr = imghdr
        tim.plver = primhdr['PLVER'].strip()
        tim.skyver = (sky.version, sky.plver)
        tim.wcsver = (wcs.version, wcs.plver)
        tim.psfver = (psf.version, psf.plver)
        tim.dq = dq
        tim.dq_bits = CP_DQ_BITS
        tim.saturation = imghdr.get('SATURATE', None)
        tim.satval = tim.saturation or 0.
        if subsky:
            tim.satval -= midsky
        if nanomaggies:
            tim.satval /= zpscale
        subh,subw = tim.shape
        tim.subwcs = tim.sip_wcs.get_subimage(tim.x0, tim.y0, subw, subh)
        mn,mx = tim.zr
        tim.ima = dict(interpolation='nearest', origin='lower', cmap='gray',
                       vmin=mn, vmax=mx)
        return tim
    
    def _read_fits(self, fn, hdu, slice=None, header=None, **kwargs):
        if slice is not None:
            f = fitsio.FITS(fn)[hdu]
            img = f[slice]
            rtn = img
            if header:
                hdr = f.read_header()
                return (img,hdr)
            return img
        return fitsio.read(fn, ext=hdu, header=header, **kwargs)

    def read_image(self, **kwargs):
        '''
        Reads the image file from disk.

        The image is read from FITS file self.imgfn HDU self.hdu.

        Parameters
        ----------
        slice : slice, optional
            2-dimensional slice of the subimage to read.
        header : boolean, optional
            Return the image header also, as tuple (image, header) ?

        Returns
        -------
        image : numpy array
            The image pixels.
        (image, header) : (numpy array, fitsio header)
            If `header = True`.
        '''
        print('Reading image from', self.imgfn, 'hdu', self.hdu)
        return self._read_fits(self.imgfn, self.hdu, **kwargs)

    def get_image_info(self):
        '''
        Reads the FITS image header and returns some summary information
        as a dictionary (image size, type, etc).
        '''
        return fitsio.FITS(self.imgfn)[self.hdu].get_info()

    def get_image_shape(self):
        '''
        Returns image shape H,W.
        '''
        return self.get_image_info()['dims']

    @property
    def shape(self):
        '''
        Returns the full shape of the image, (H,W).
        '''
        return self.get_image_shape()
    
    def read_image_primary_header(self, **kwargs):
        '''
        Reads the FITS primary (HDU 0) header from self.imgfn.

        Returns
        -------
        primary_header : fitsio header
            The FITS header
        '''
        return fitsio.read_header(self.imgfn)

    def read_image_header(self, **kwargs):
        '''
        Reads the FITS image header from self.imgfn HDU self.hdu.

        Returns
        -------
        header : fitsio header
            The FITS header
        '''
        return fitsio.read_header(self.imgfn, ext=self.hdu)

    def read_dq(self, **kwargs):
        '''
        Reads the Data Quality (DQ) mask image.
        '''
        return None

    def read_invvar(self, clip=True, **kwargs):
        '''
        Reads the inverse-variance (weight) map image.
        '''
        return None

    def get_wcs(self):
        return self.read_pv_wcs()

    def read_pv_wcs(self):
        '''
        Reads the WCS header, returning an `astrometry.util.util.Sip` object.
        '''
        from astrometry.util.util import Sip

        print('Reading WCS from', self.pvwcsfn)
        wcs = Sip(self.pvwcsfn)
        dra,ddec = self.decals.get_astrometric_zeropoint_for(self)
        r,d = wcs.get_crval()
        print('Applying astrometric zeropoint:', (dra,ddec))
        wcs.set_crval((r + dra, d + ddec))
        hdr = fitsio.read_header(self.pvwcsfn)
        wcs.version = hdr.get('LEGPIPEV', '')
        if len(wcs.version) == 0:
            wcs.version = hdr.get('TRACTORV', '').strip()
            if len(wcs.version) == 0:
                wcs.version = str(os.stat(self.pvwcsfn).st_mtime)
        wcs.plver = hdr.get('PLVER', '').strip()
        return wcs
    
    def read_sky_model(self):
        '''
        Reads the sky model, returning a Tractor Sky object.
        '''
        print('Reading sky model from', self.skyfn)
        hdr = fitsio.read_header(self.skyfn)
        skyclass = hdr['SKY']
        clazz = get_class_from_name(skyclass)

        if getattr(clazz, 'from_fits', None) is not None:
            fromfits = getattr(clazz, 'from_fits')
            skyobj = fromfits(self.skyfn, hdr)
        else:
            fromfits = getattr(clazz, 'fromFitsHeader')
            skyobj = fromfits(hdr, prefix='SKY_')

        skyobj.version = hdr.get('LEGPIPEV', '')
        if len(skyobj.version) == 0:
            skyobj.version = hdr.get('TRACTORV', '').strip()
            if len(skyobj.version) == 0:
                skyobj.version = str(os.stat(self.skyfn).st_mtime)
        skyobj.plver = hdr.get('PLVER', '').strip()
        return skyobj

    def run_calibs(self, pvastrom=True, psfex=True, sky=True, se=False,
                   funpack=False, fcopy=False, use_mask=True,
                   force=False, just_check=False, git_version=None):
        '''
        Runs any required calibration processes for this image.
        '''
        print('run_calibs for', self)
        print('(not implemented)')
        pass

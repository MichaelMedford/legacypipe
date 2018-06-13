from __future__ import print_function
import numpy as np

import astropy.time

from legacypipe.image import LegacySurveyImage, CP_DQ_BITS

'''
Code specific to images from the Zwicky Transient Facility (ZTF).
'''

def CreateCCDTable():



class ZtfImage(LegacySurveyImage):
    '''
    A LegacySurveyImage subclass to handle images from the Dark Energy
    Camera, DECam, on the Blanco telescope.
    '''
    def __init__(self, survey, t):
        super(DecamImage, self).__init__(survey, t)
        # Adjust zeropoint for exposure time
        self.ccdzpt += 2.5 * np.log10(self.exptime)

    def read_invvar(self, **kwargs):
        return self.read_invvar_clipped(**kwargs)

    glowmjd = astropy.time.Time('2014-08-01').utc.mjd

    def get_good_image_subregion(self):
        x0,x1,y0,y1 = None,None,None,None

        # Handle 'glowing' edges in DES r-band images
        # aww yeah
        if self.band == 'r' and (
                ('DES' in self.imgfn) or ('COSMOS' in self.imgfn) or
                (self.mjdobs < DecamImage.glowmjd)):
            # Northern chips: drop 100 pix off the bottom
            if 'N' in self.ccdname:
                print('Clipping bottom part of northern DES r-band chip')
                y0 = 100
            else:
                # Southern chips: drop 100 pix off the top
                print('Clipping top part of southern DES r-band chip')
                y1 = self.height - 100

        # Clip the bad half of chip S7.
        # The left half is OK.
        if self.ccdname == 'S7':
            print('Clipping the right half of chip S7')
            x1 = 1023

        return x0,x1,y0,y1

    def remap_dq(self, dq, hdr):
        '''
        Called by get_tractor_image() to map the results from read_dq
        into a bitmask.
        '''
        from distutils.version import StrictVersion
        # The format of the DQ maps changed as of version 3.5.0 of the
        # Community Pipeline.  Handle that here...
        primhdr = self.read_primary_header(self.dqfn)
        plver = primhdr['PLVER'].strip()
        plver = plver.replace('V','')
        plver = plver.replace('DES ', '')
        plver = plver.replace('+1', 'a1')
        if StrictVersion(plver) >= StrictVersion('3.5.0'):
            dq = self.remap_dq_cp_codes(dq, hdr)
        else:
            from legacypipe.image import CP_DQ_BITS
            dq = dq.astype(np.int16)
            # Un-set the SATUR flag for pixels that also have BADPIX set.
            bothbits = CP_DQ_BITS['badpix'] | CP_DQ_BITS['satur']
            I = np.flatnonzero((dq & bothbits) == bothbits)
            if len(I):
                print('Warning: un-setting SATUR for', len(I),
                      'pixels with SATUR and BADPIX set.')
                dq.flat[I] &= ~CP_DQ_BITS['satur']
                assert(np.all((dq & bothbits) != bothbits))
        return dq

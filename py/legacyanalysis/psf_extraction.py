#!/usr/env python

import numpy as np
import scipy.ndimage

import astropy.wcs
import astropy.io
import astropy.convolution
import astropy.modeling

import warnings

from sklearn.neighbors import NearestNeighbors


def fit_2d_gaussian(img):
    '''
    Fit a 2D Gaussian to an image. The 2D Gaussian model includes a center
    (x, y), a standard deviation along each axis, a rotation angle and an
    overall amplitude.

    Input:
      img  A 2D numpy array representing the image to be fit.

    Output:
      model_fit  An astropy.modeling.models.Gaussian2D object. Calling
                 `model_fit(x,y)` will return the value of the model Gaussian
                 at (x, y). See the astropy documentation for more details on
                 how to interact with this class.
    '''

    shape = img.shape
    y, x = np.mgrid[:shape[1], :shape[0]]

    # Fit a 2D Gaussian to the data
    model_guess = astropy.modeling.models.Gaussian2D(
        x_mean=((shape[0]-1.)/2.),
        y_mean=((shape[1]-1.)/2.),
        x_stddev=1.,
        y_stddev=1.,
        amplitude=np.max(img)
    )

    fitter = astropy.modeling.fitting.LevMarLSQFitter()

    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('default')
        # TODO: bound the model parameters to reasonable values.
        model_fit = fitter(model_guess, x, y, img)

    return model_fit


def img_center_of_mass(img, img_mask):
    '''
    '''

    idx = ~np.isfinite(img) | (img_mask != 0) # Determine image mask
    idx |= idx[:,::-1] | idx[::-1,:] # Make mask symmetric under parity flips
    img_clean = np.empty(img.shape, dtype='f8')
    img_clean[:] = img[:]
    img_clean[idx] = 0.

    return scipy.ndimage.measurements.center_of_mass(img_clean)


def gen_centered_weights(shape, sigma, n_sigma_clip=3.):
    '''
    Return a weight image that weights pixels towards the center of the image
    more strongly than pixels away from the center.
    '''
    w = np.array(astropy.convolution.Gaussian2DKernel(
        sigma, x_size=shape[0], y_size=shape[1],
        mode='oversample', factor=5
    ))

    w /= np.max(w)
    w[w < np.exp(-0.5 * n_sigma_clip**2.)] = 0.

    return w


def recenter_postage_stamps(exposure_img, weight_img, mask_img, star_x, star_y,
                            ps_exposure, ps_weight, ps_mask, **kwargs):
    '''
    Recenter a stack of postage stamps, trying to properly centroid each star.
    Should work for small shifts (< 1 pixel). Calculates a weighted center of
    mass for each postage stamp (the weighting ignores pixels away from the
    center of the image), and then goes back into the original exposure image
    and extracts the stars again.
    '''

    max_shift = kwargs.pop('max_shift', 2.)

    # Weight to apply to each image before calculating center of mass
    w_cent = gen_centered_weights(ps_exposure.shape[1:],
                                  2.*max_shift,
                                  n_sigma_clip=1.)

    dxy = []
    star_x_cent, star_y_cent = [], []

    # Calculate the weighted center of mass of each postage stamp
    for ps_img, ps_mask in zip(ps_exposure, ps_mask):
        dxy.append(img_center_of_mass(ps_img*w_cent, ps_mask))

    dxy = np.array(dxy)
    dxy[:,0] -= 0.5 * float(ps_exposure.shape[1]-1.)
    dxy[:,1] -= 0.5 * float(ps_exposure.shape[2]-1.)

    # Find the stars that have only small shifts
    idx_good = np.all((np.abs(dxy) < max_shift) & np.isfinite(dxy), axis=1)

    # Apply the small shifts to the stellar positions
    star_x_cent = np.array(star_x)
    star_y_cent = np.array(star_y)
    star_x_cent[idx_good] += dxy[idx_good, 0]
    star_y_cent[idx_good] += dxy[idx_good, 1]

    ret = extract_stars(exposure_img, weight_img, mask_img,
                        star_x_cent, star_y_cent, **kwargs)

    return ret


def sinc_shift_image(img, dx, dy):
    '''
    Shift a real-valued image by (dx,dy), using the DFT shift theorem.

    Input:
      img  A 2D image, represented by a 2D, real-valued numpy array.
      dx   The shift along the x-axis, in pixels
      dy   The shift along the y-axis, in pixels

    Output:
      A shifted copy of the image, as a 2D numpy array.
    '''

    img_dft = np.fft.fft2(img)
    img_dft = scipy.ndimage.fourier.fourier_shift(img_dft, (dx,dy))
    return np.real(np.fft.ifft2(img_dft))


def gen_stellar_flux_predictor(star_flux, star_ps1_mag,
                               star_x, star_y, ccd_shape,
                               psf_coeffs):
    n_stars = star_flux.size
    #print 'CCD Shape:', ccd_shape

    # Calculate corrections to fluxes, by summing the PSF at the location of
    # each star
    psf_norm = np.empty(n_stars, dtype='f8')

    for k in range(n_stars):
        # Evaluate the PSF at the location of the star
        psf_model = eval_psf(psf_coeffs, star_x[k], star_y[k], ccd_shape)
        psf_norm[k] = np.sum(psf_model)

    print 'PSF Norm:', psf_norm

    star_flux_corr = star_flux * psf_norm

    # TODO: Automatic computation of PSF normalization
    # TODO: Automatic choice of bands to use

    # Convert PS1 magnitude to flux, where 20th mag corresponds to a flux of 1
    ps1_flux = 10.**(-(star_ps1_mag-20.) / 2.5)

    # The model is that the fitted flux is a linear combination of the fluxes
    # in the PS1 bands, plus a zero point flux. The design matrix is therefore
    # given by
    #
    #   A = [[1 g_0 r_0 i_0 z_0 y_0],
    #        [1 g_1 r_1 i_1 z_1 y_1],
    #                  ...
    #        [1 g_n r_n i_n z_n y_n]] ,
    #
    # where n is the number of stars, while the parameter matrix is given by
    #
    #   x = [f_zp c_g c_r c_i c_z c_y] ,
    #
    # and the data matrix is given by
    #
    #   b = [f_0 f_1 ... f_n] ,
    #
    # where f_k is the flux of star k.

    n_stars = star_flux.size

    A = np.empty((n_stars, 6), dtype='f8')
    A[:,0] = 1.
    A[:,1:] = ps1_flux[:]

    # Use only stars with 5-band photometry
    idx_good = np.all((star_ps1_mag > 1.) & (star_ps1_mag < 26.), axis=1)
    idx_good &= np.isfinite(star_flux)

    print idx_good
    print '# of good stars: {}'.format(np.sum(idx_good))

    A = A[idx_good]
    b = star_flux_corr[idx_good]

    # Set errors in fitted fluxes at 5%
    #sigma = b * 0.05
    #sqrt_w = 1. / sigma
    #A *= sqrt_w[:,None]
    #b *= sqrt_w[:]

    # Remove NaN and Inf values
    A[~np.isfinite(A)] = 0.
    b[~np.isfinite(b)] = 0.

    # Execute least squares
    coeffs = np.linalg.lstsq(A, b)[0]
    zp = coeffs[0]
    c = coeffs[1:]

    print 'Flux fit coefficients:'
    print coeffs
    print ''

    def PS1_mag_to_fit_flux(m_p1):
        f_p1 = 10.**(-(m_p1-20.) / 2.5)
        return zp + np.einsum('k,jk->j', c, f_p1)

    print star_ps1_mag[idx_good][:3]
    f_resid = (PS1_mag_to_fit_flux(star_ps1_mag[idx_good]) - star_flux_corr[idx_good]) / star_flux_corr[idx_good]

    print 'Residuals:'
    print f_resid
    print 'Residual percentiles:'
    pctiles = [1., 5., 10., 20., 50., 80., 90., 95., 99.]
    for p,r in zip(pctiles, np.percentile(f_resid, pctiles)):
        print '  {: 2d} -> {:.3f}'.format(int(p), r)
    print ''

    return PS1_mag_to_fit_flux


def filter_close_points(x, y, r):
    '''
    Filter a list of points in 2D, flagging points that are too close to another
    point.

    Inputs:
      x  x-coordinates of points
      y  y-coordinates of points
      r  Radius at which to filter points

    Outputs:
      keep_idx  An boolean array, with True for points that have no near
                neighbor, and False for points that do.
    '''

    xy = np.vstack([x,y]).T
    nn = NearestNeighbors(radius=r)
    nn.fit(xy)
    idx_collection = nn.radius_neighbors(radius=r, return_distance=False)

    keep_idx = np.ones(x.size, dtype=np.bool)

    for idx in idx_collection:
        keep_idx[idx] = 0

    return keep_idx


def eval_psf(psf_coeffs, star_x, star_y, ccd_shape):
    x = star_x / float(ccd_shape[0])
    y = star_y / float(ccd_shape[1])

    psf_img = np.empty((psf_coeffs.shape[1], psf_coeffs.shape[2]), dtype='f8')

    # TODO: Generalize this to arbitrary orders of x,y
    psf_img[:,:] = psf_coeffs[0,:,:]
    psf_img[:,:] += psf_coeffs[1,:,:] * x
    psf_img[:,:] += psf_coeffs[2,:,:] * y
    psf_img[:,:] += psf_coeffs[3,:,:] * x*x
    psf_img[:,:] += psf_coeffs[4,:,:] * y*y
    psf_img[:,:] += psf_coeffs[5,:,:] * x*y

    return psf_img




def fit_star_params(psf_coeffs, star_x, star_y,
                    ps_exposure, ps_weight, ps_mask, ccd_shape,
                    sky_mean=0., sky_sigma=0.5,
                    stellar_flux_mean=0., stellar_flux_sigma=np.inf):
    '''
    Fit stellar flux and sky brightness, given a PSF model.
    '''

    # Evaluate the PSF at the location of the star
    psf_val = eval_psf(psf_coeffs, star_x, star_y, ccd_shape)
    #psf_val /= np.sum(psf_val)
    psf_val.shape = (psf_val.size,)

    # Normalize the stellar flux priors
    psf_norm = np.sum(psf_val)
    stellar_flux_mean = stellar_flux_mean / psf_norm
    stellar_flux_sigma = stellar_flux_sigma / psf_norm
    print 'stellar flux prior: {:.5f} +- {:.5f}'.format(stellar_flux_mean, stellar_flux_sigma)

    # Calculate the square root of the weight
    sqrt_w = np.sqrt(ps_weight.flat)
    #sqrt_w = np.ones(ps_weight.size, dtype='f8')
    sqrt_w[ps_mask.flat != 0] = 0.

    # The linear least squares design and data matrices
    A = np.vstack([sqrt_w * psf_val, sqrt_w]).T
    b = sqrt_w * ps_exposure.flat

    # Extend the design and data matrices to incorporate priors
    A_priors = np.array([
        [1./stellar_flux_sigma, 0.], # Prior on stellar flux
        [0., 1./sky_sigma]           # Prior on sky level
    ])
    b_priors = np.array([
        stellar_flux_mean/stellar_flux_sigma, # Prior on stellar flux
        sky_mean/sky_sigma                    # Prior on sky level
    ])
    A = np.vstack([A, A_priors])
    b = np.hstack([b, b_priors])

    print ''
    print 'A:'
    print A
    print ''
    print 'b:'
    print b
    print ''

    # Remove NaN and Inf values
    A[~np.isfinite(A)] = 0.
    b[~np.isfinite(b)] = 0.

    # Execute least squares
    a0, a1 = np.linalg.lstsq(A, b)[0]

    return a0, a1


def fit_psf_coeffs(star_flux, star_sky,
                   star_x, star_y, ccd_shape,
                   ps_exposure, ps_weight, ps_mask,
                   sigma_nonzero_order=0.1):
    n_stars, n_x, n_y = ps_exposure.shape

    # Scale coordinates so that x,y are each in range [0,1]
    x = star_x / float(ccd_shape[0])
    y = star_y / float(ccd_shape[1])

    # Normalize counts (by removing sky background and dividing out stellar flux)
    img_zeroed = ps_exposure - star_sky[:,None,None]
    img_zeroed[ps_mask != 0] = 0.

    # Transform pixel weights
    sqrt_w = np.sqrt(ps_weight)
    sqrt_w[ps_mask != 0] = 0. # Zero weight for masked pixels

    # Design matrix
    A_base = np.empty((n_stars+6, 6), dtype='f8') # without per-pixel weights
    A = np.empty((n_stars+6, 6), dtype='f8') # with weights - will be updated for each PSF pixel

    # TODO: Generalize this to arbitrary orders of x,y
    A_base[:n_stars,0] = 1.
    A_base[:n_stars,1] = x
    A_base[:n_stars,2] = y
    A_base[:n_stars,3] = x**2.
    A_base[:n_stars,4] = y**2.
    A_base[:n_stars,5] = x*y

    # Data matrix
    b = np.zeros(n_stars+6, dtype='f8')

    # Remove masked pixels
    mask_pix = np.where(ps_mask != 0)[0]
    A_base[mask_pix] = 0.

    print '# of masked pixels: {}'.format(mask_pix.size)

    # Priors
    A_base[-6:,:] = np.diag(np.ones(6, dtype='f8'))

    psf_coeffs = np.empty((6, n_x, n_y), dtype='f8')

    # Loop over pixels in PSF, fitting coefficients for each pixel separately
    for j in range(n_x):
        for k in range(n_y):
            # Design matrix
            A[:] = A_base[:]
            #A[:n_stars,:] *= sqrt_w[:,None,j,k]
            A[-6] *= 0. # Prior on the zeroeth-order term
            A[-5:] *= 1 / sigma_nonzero_order # Prior on higher-order terms

            # Data matrix
            b[:n_stars] = img_zeroed[:,j,k] * star_flux[:]# * sqrt_w[:n_stars,j,k]
            b[mask_pix] = 0.

            # Remove NaN and Inf values
            A[~np.isfinite(A)] = 0.
            b[~np.isfinite(b)] = 0.

            # Execute least squares
            psf_coeffs[:,j,k] = np.linalg.lstsq(A, b)[0]

    return psf_coeffs


def normalize_psf_coeffs(psf_coeffs):
    '''
    Returns a copy of the PSF coefficients, in which the zeroeth-order PSF
    sums to unity. With the higher-order terms (which encode the variation
    across the CCD) added in, the PSF may not sum to unity.

    Input:
      psf_coeffs  The polynomial coefficients for each PSF pixel. The shape of
                  the output is (polynomial order, x, y).

    Output:
      psf_coeffs  A normalized copy of the input.
    '''

    norm = 1. / np.sum(psf_coeffs[0])

    return psf_coeffs * norm


def guess_psf(ps_exposure, ps_weight, ps_mask):
    '''
    Guess the PSF by stacking stars with no masked pixels.
    '''

    # Select postage stamps with no masked pixels
    idx = np.all(np.all(ps_mask == 0, axis=1), axis=1)
    tmp = ps_exposure[idx]

    # Normalize sum of each selected postage stamp to one
    tmp /= np.sum(np.sum(tmp, axis=1), axis=1)[:,None,None]

    # Take the median of the normalized postage stamps
    psf_guess = np.median(ps_exposure[idx], axis=0)

    # Normalize the guess to unity
    psf_guess /= np.sum(psf_guess)

    return psf_guess



def extract_stars(exposure_img, weight_img, mask_img, star_x, star_y,
                  width=int(np.ceil(5./0.263)), buffer_width=10, avoid_edges=1):
    '''
    Extracts postage stamps of stars from a CCD image.

    Input:
      exposure_img  CCD counts image.
      weight_img    CCD weight image.
      mask_img      CCD mask image.
      star_x        x-coordinate of each star on the CCD (in pixels - can be fractional).
      star_y        y-coordinate of each star on the CCD (in pixels - can be fractional).
      width         Width/height of the postage stamps.
      buffer_width  # of pixels to expand postage stamps by on each edge during
                    intermediate processing.
      avoid_edges   # of pixels on each edge of the CCD to avoid.

    Returns:
      ps_stack  An array of shape (3, n_stars, width, height). The zeroeth axis
                of the array corresponds to (exposure, weight, mask). The last
                two axes correspond to the width and height of each postage stamp.
    '''
    n_stars = star_x.size

    # Create empty stack of images
    w_ps = 2 * (width+buffer_width) + 1  # The width/height of the postage stamp, before final trimming
    ps_stack = np.zeros((3, n_stars, w_ps, w_ps), dtype='f8')
    ps_stack[2,:,:,:] = 1. # Initialize the mask to one (e.g., everything bad)

    # Determine amount to shift each star to center it on a pixel
    x_floor, y_floor = np.floor(star_x).astype('i4'), np.floor(star_y).astype('i4')
    dx = -(star_x - x_floor - 0.5)
    dy = -(star_y - y_floor - 0.5)

    # For each star, determine rectangle to copy from
    # the exposure (the "source" image), and the rectangle
    # to paste into in the postage stamp (the "destination" image)
    src_j0 = x_floor - (width+buffer_width)
    src_j1 = x_floor + (width+buffer_width) + 1
    src_k0 = y_floor - (width+buffer_width)
    src_k1 = y_floor + (width+buffer_width) + 1

    dst_j0 = np.zeros(n_stars, dtype='i4')
    dst_j1 = np.ones(n_stars, dtype='i4') * w_ps
    dst_k0 = np.zeros(n_stars, dtype='i4')
    dst_k1 = np.ones(n_stars, dtype='i4') * w_ps

    # Clip source rectangles at edges of exposure image, and shrink
    # destination rectangles accordingly
    idx = src_j0 < avoid_edges
    dst_j0[idx] = avoid_edges-src_j0[idx]
    src_j0[idx] = avoid_edges

    idx = src_j1 > exposure_img.shape[0] - avoid_edges
    dst_j1[idx] = exposure_img.shape[0] - avoid_edges - src_j1[idx]
    src_j1[idx] = exposure_img.shape[0] - avoid_edges

    idx = src_k0 < avoid_edges
    dst_k0[idx] = avoid_edges-src_k0[idx]
    src_k0[idx] = avoid_edges

    idx = src_k1 > exposure_img.shape[1] - avoid_edges
    dst_k1[idx] = exposure_img.shape[1] - avoid_edges - src_k1[idx]
    src_k1[idx] = exposure_img.shape[1] - avoid_edges

    kern = astropy.convolution.Box2DKernel(3)

    # Extract each star
    for i, (sj0,sj1,sk0,sk1,dj0,dj1,dk0,dk1) in enumerate(zip(src_j0,src_j1,
                                                              src_k0,src_k1,
                                                              dst_j0,dst_j1,
                                                              dst_k0,dst_k1)):
        #print '{}: ({},{},{},{}) --> ({},{},{},{})'.format(i,sj0,sj1,sk0,sk1,dj0,dj1,dk0,dk1)

        # Don't include postage stamps that are more than 50% clipped
        if (  (dj0 > 0.5*w_ps) or (dj1 < -0.5*w_ps)
           or (dk0 > 0.5*w_ps) or (dk1 < -0.5*w_ps)):
            continue


        # Extract star from exposure, weight and mask images
        tmp_exposure = exposure_img[sj0:sj1,sk0:sk1]
        tmp_weight = weight_img[sj0:sj1,sk0:sk1]
        tmp_mask = mask_img[sj0:sj1,sk0:sk1]

        # Skip star if no good pixels
        idx_use = (tmp_mask == 0)

        if np.all(~idx_use):
            continue

        # Find non-center pixels
        #s = idx_use.shape
        #idx_noncenter = np.ones(s, dtype=np.bool)
        #idx_noncenter[s[0]/4:3*s[0]/4, s[1]/4:int(3./4.*s[1])]

        # Copy star into postage stamp stack
        ps_stack[0,i,dj0:dj1,dk0:dk1] = tmp_exposure - np.median(tmp_exposure[idx_use])
        ps_stack[0,i] = sinc_shift_image(ps_stack[0,i], dx[i], dy[i])

        ps_stack[1,i] = np.median(tmp_weight[idx_use])
        ps_stack[1,i,dj0:dj1,dk0:dk1] = tmp_weight
        ps_stack[1,i] = sinc_shift_image(ps_stack[1,i], dx[i], dy[i])

        ps_stack[2,i,dj0:dj1,dk0:dk1] = tmp_mask
        ps_stack[2,i] = astropy.convolution.convolve(ps_stack[2,i], kern, boundary='extend')#white_tophat(ps_stack[2,i], size=3, mode='nearest')

    # Clip edge pixels off of postage stamps and return result
    return ps_stack[:, :, buffer_width:w_ps-buffer_width, buffer_width:w_ps-buffer_width]


def filter_postage_stamps(ps_mask, min_pixel_fraction=0.5):
    '''
    Return the indices of the stellar postage stamps that have enough good
    pixels to use.

    Inputs:
      ps_mask             Postage stamp of the mask in the vicinity of the star.
      min_pixel_fraction  Minimum fraction of good pixels to accept a stellar
                          postage stamp.

    Output:
      keep_idx  The indices of the postge stamps with enough good pixels.
    '''

    n_pix = ps_mask.shape[1] * ps_mask.shape[2]
    n_good_pix = np.sum(np.sum(ps_mask == 0, axis=1), axis=1)
    idx = (n_good_pix > min_pixel_fraction * n_pix)

    return idx


def get_star_locations(ps1_table, wcs, ccd_shape, min_separation=10./0.263):
    '''
    Get pixel coordinates of PS1 stars that fall on a given DECam CCD exposure.

    Inputs:
      ps1_table  A table of PS1 detections that fall on the given exposure.
      wcs        A World Coordinate System object describing the projection
                 of the CCD.
      ccd_shape  The shape (in pixels) of the CCD: (x extent, y extent).

    Optional parameters:
      min_separation  Minimum separation (in pixels) between stars. Stars closer
                      to one another than this distance will be rejected.

    Outputs:
      star_x  x-coordinates (in pixels) of the selected PS1 stars on the CCD.
      star_y  y-coordinates (in pixels) of the selected PS1 stars on the CCD.
      star_ps1_mag  PS1 grizy magnitudes of stars.
    '''

    # Get stellar pixel coordinates
    star_y, star_x = wcs.wcs_world2pix(ps1_table['RA'], ps1_table['DEC'], 0)   # 0 is the coordinate in the top left (the numpy, but not FITS standard)

    # Filter stars that are off the CCD
    idx = ((star_x > -min_separation) & (star_x < ccd_shape[0] + min_separation) &
           (star_y > -min_separation) & (star_y < ccd_shape[1] + min_separation))

    star_x = star_x[idx]
    star_y = star_y[idx]
    ps1_table = ps1_table[idx]

    # Filter stars that are too close to one another
    idx = filter_close_points(star_x, star_y, r=min_separation)

    # Filter stars that don't pass quality cuts
    idx &= filter_ps1_quality(ps1_table)

    return star_x[idx], star_y[idx], ps1_table['MEAN'][idx]


def filter_ps1_quality(ps1_table):
    '''
    Return the indices of PS1 objects that pass a set of cuts, which select for
    compact sources detected in multiple exposures.

    Input:
      ps1_table: A record array of PS1 objects, containing at least:
                   - 'NMAG_OK' (number of good detections in each band)
                   - 'MEAN'    (mean psf mag in each band over multiple detections)
                   - 'MEAN_AP' (mean aperture mag in each band over multiple detections)

    Output:
      keep_idx  A boolean array, containing True for stars that pass the cuts,
                and False otherwise.
    '''

    idx = ((np.sum(ps1_table['NMAG_OK'], axis=1) >= 5) &
           (np.sum(ps1_table['MEAN'] - ps1_table['MEAN_AP'] < 0.1, axis=1) >= 2))

    return idx


def get_ps1_stars_for_ccd(wcs, ccd_shape, min_separation):
    '''
    Returns pixel coordinates for stars detected by PS1 that fall on the CCD.

    Inputs:
      wcs             A World Coordinate System object describing the projection
                      of the CCD.
      ccd_shape       The shape (in pixels) of the CCD: (x extent, y extent).
      min_separation  Minimum separation (in pixels) between stars. Stars closer
                      to one another than this distance will be rejected.

    Ouptuts:
      star_x  x-coordinates of the PS1 stars (in pixels).
      star_y  y-coordinates of the PS1 stars (in pixels).
      star_ps1_mag  PS1 grizy magnitudes of stars.
    '''

    # Load locations of PS1 stars
    fname = 'psftest/ps1stars-c4d_150109_051822.fits'
    ps1_table = astropy.io.fits.getdata(fname, 1)
    # TODO: Replace this with call to ps1cat.ps1cat

    star_x, star_y, star_ps1_mag = get_star_locations(ps1_table, wcs, ccd_shape,
                                                      min_separation=min_separation)

    return star_x, star_y, star_ps1_mag


def calc_star_chisq(psf_coeffs, ps_exposure, ps_weight, ps_mask,
                    star_x, star_y, star_flux, sky_level, ccd_shape):
    '''
    Calculate the mean squared deviation of each postage stamp's pixels from the
    modeled flux (based on the PSF model, fitted stellar flux and sky level),
    weighted by the exposure weights.

    Inputs:
      psf_coeffs
      ps_exposure
      ps_weight
      ps_mask
      star_x
      star_y
      star_flux
      sky_level
      ccd_shape

    Outputs:
      psf_resid  Mean squared weighted residuals between the postage stamps and
                 the modeled flux.
    '''

    x = star_x / float(ccd_shape[0])
    y = star_y / float(ccd_shape[1])

    psf_img = np.zeros(ps_exposure.shape, dtype='f8')
    psf_img += psf_coeffs[0,None,:,:]
    psf_img += psf_coeffs[1,None,:,:] * x[:,None,None]
    psf_img += psf_coeffs[2,None,:,:] * y[:,None,None]
    psf_img += psf_coeffs[3,None,:,:] * x[:,None,None] * x[:,None,None]
    psf_img += psf_coeffs[4,None,:,:] * y[:,None,None] * y[:,None,None]
    psf_img += psf_coeffs[5,None,:,:] * x[:,None,None] * y[:,None,None]

    psf_img *= star_flux[:,None,None]
    psf_img += sky_level[:,None,None]

    psf_resid = psf_img - ps_exposure
    psf_resid *= psf_resid * ps_weight
    psf_resid[(ps_mask != 0) | ~np.isfinite(psf_resid)] = 0.
    psf_resid = np.sum(np.sum(psf_resid, axis=1), axis=1)
    psf_resid /= float(ps_exposure.shape[1] * ps_exposure.shape[2])

    return psf_resid


def extract_psf(exposure_img, weight_img, mask_img, wcs,
                min_separation=50., min_pixel_fraction=0.5, n_iter=1,
                psf_halfwidth=31, buffer_width=10, avoid_edges=1,
                star_chisq_threshold=2., max_star_shift=3.,
                return_postage_stamps=False):
    '''
    Extract the PSF from a CCD exposure, using a pixel basis. Each pixel is
    represented as a polynomial in (x,y), where x and y are the pixel
    coordinates on the CCD.

    Inputs:
      exposure_img  CCD counts image.
      weight_img    CCD weight image.
      mask_img      CCD mask image.
      wcs           A World Coordinate System object describing the projection
                    of the CCD.

    Optional parameters:
      n_iter              # of iterations to run for. Each iteration consists of
                          fitting the stellar fluxes and local sky levels, given
                          the current PSF fit, and then updating the PSF fit,
                          based on the stars.
      psf_halfwidth       The width/height of the PSF image will be 2*psf_halfwidth+1.
      min_separation      Minimum separation (in pixels) between stars. Stars closer
                          to one another than this distance will be rejected.
      min_pixel_fraction  Minimum fraction of pixels around a star that must be
                          unmasked in order for the star to be used for the fit.
      buffer_width        # of pixels to expand postage stamps by on each edge
                          during intermediate processing.
      avoid_edges         # of pixels on each edge of the CCD to avoid.
      star_chisq_threshold   chi^2/dof at which stars will not be used to derive
                             PSF fit.
      max_star_shift         The maximum shift (in pixels) that can be applied
                             to the position of any star (based on an estimate
                             of the star's centroid location).
      return_postage_stamps  If True, return a stack of postage stamps of the
                             stars used in the fit.

    Output:
      psf_coeffs  The polynomial coefficients for each PSF pixel. The shape of
                  the output is (polynomial order, x, y).

    If return_postage_stamps == True, a dictionary containing the following
    keys is also returned:
      ps_exposure   Counts postage stamps of the stars used in the fit. The
                    shape is (# of stars, x, y).
      ps_weight     Weight postage stamps for the stars used in the fit. The
                    shape is (# of stars, x, y).
      ps_mask       Mask postage stamps for the stars used in the fit. The shape
                    is (# of stars, x, y).
      star_x        x-coordinates (in pixels) on the CCD of the stars used in
                    the fit.
      star_y        y-coordinates (in pixels) on the CCD of the stars used in
                    the fit.
      star_PS1_mag  PS1 grizy magnitudes of the stars.
      stellar_flux  Flux of each star (as a multiple of the local PSF) used in
                    the fit.
      sky_level     The local sky level for each star used in the fit.
    '''

    # Select stars (from PS1)
    ccd_shape = exposure_img.shape
    star_x, star_y, star_ps1_mag = get_ps1_stars_for_ccd(wcs, ccd_shape,
                                                         min_separation=min_separation)

    # Extract centered postage stamps of stars, sinc shifting stars as necessary
    ps_exposure, ps_weight, ps_mask = extract_stars(exposure_img, weight_img,
                                                    mask_img, star_x, star_y,
                                                    width=psf_halfwidth,
                                                    buffer_width=buffer_width,
                                                    avoid_edges=avoid_edges)

    # Recenter the postage stamps
    ps_exposure, ps_weight, ps_mask = recenter_postage_stamps(
        exposure_img, weight_img, mask_img,
        star_x, star_y,
        ps_exposure, ps_weight, ps_mask,
        max_shift=max_star_shift,
        width=psf_halfwidth,
        buffer_width=buffer_width,
        avoid_edges=avoid_edges
    )

    # Filter out stars that are more than a certain percent masked
    idx = filter_postage_stamps(ps_mask, min_pixel_fraction=min_pixel_fraction)
    ps_exposure = ps_exposure[idx]
    ps_weight = ps_weight[idx]
    ps_mask = ps_mask[idx]
    star_x = star_x[idx]
    star_y = star_y[idx]
    star_ps1_mag = star_ps1_mag[idx]

    # Find indices of stars with no masking at all
    idx_unmasked = filter_postage_stamps(ps_mask, min_pixel_fraction=0.99999)
    print '{} completely unmasked stars.'.format(np.sum(idx_unmasked))

    # Guess the PSF by median-stacking pristine postage stamps (no masked pixels)
    psf_guess = guess_psf(ps_exposure, ps_weight, ps_mask)

    # The fit parameters
    n_stars = ps_exposure.shape[0]
    psf_coeffs = np.zeros((6, ps_exposure.shape[1], ps_exposure.shape[2]), dtype='f8')
    psf_coeffs[0,:,:] = psf_guess[:,:]
    stellar_flux = np.empty(n_stars, dtype='f8')
    sky_level = np.empty(n_stars, dtype='f8')
    stellar_flux[:] = np.nan
    sky_level[:] = np.nan

    # Fit a 2D Gaussian to the PSF guess, to be used as a prior on the
    # zeroeth-order PSF coefficients.
    #gauss_psf_prior = fit_2d_gaussian(psf_coeffs[0,:,:])
    #print gauss_psf_prior

    stellar_flux_mean = np.zeros(n_stars, dtype='f8')
    stellar_flux_sigma = np.empty(n_stars, dtype='f8')
    stellar_flux_sigma[:] = np.inf

    for j in range(n_iter):
        # Fit the flux and local sky level for each star
        for k in range(n_stars):
            stellar_flux[k], sky_level[k] = fit_star_params(
                psf_coeffs,
                star_x[k], star_y[k],
                ps_exposure[k], ps_weight[k],
                ps_mask[k], ccd_shape,
                sky_sigma=0.05,
                stellar_flux_mean=stellar_flux_mean[k],
                stellar_flux_sigma=stellar_flux_sigma[k]
            )

        # Flag stars with bad chi^2/dof
        star_chisq = calc_star_chisq(psf_coeffs, ps_exposure, ps_weight, ps_mask,
                                     star_x, star_y, stellar_flux, sky_level,
                                     ccd_shape)
        idx_chisq = (star_chisq < star_chisq_threshold)

        print 'Rejected stars:'
        print np.where(~idx_chisq)[0]

        print 'Rejected {} of {} stars.'.format(np.sum(~idx_chisq), idx_chisq.size)

        # Update the prior on stellar flux
        idx = idx_chisq & idx_unmasked
        flux_predictor = gen_stellar_flux_predictor(
            stellar_flux[idx], star_ps1_mag[idx],
            star_x[idx], star_y[idx],
            ccd_shape, psf_coeffs
        )
        stellar_flux_mean[:] = flux_predictor(star_ps1_mag)
        stellar_flux_sigma[:] = np.sqrt(stellar_flux_mean)

        # Fit the PSF coefficients in each pixel
        if j == 0:
            idx = idx_chisq & idx_unmasked
        else:
            idx = idx_chisq
        psf_coeffs = fit_psf_coeffs(stellar_flux[idx], sky_level[idx],
                                    star_x[idx], star_y[idx],
                                    ccd_shape, ps_exposure[idx],
                                    ps_weight[idx], ps_mask[idx])

        # Normalize the PSF
        psf_coeffs = normalize_psf_coeffs(psf_coeffs)

        # Update the 2D Gaussian (which is a prior on the zeroeth-order
        # PSF coefficients)
        #gauss_psf_prior = fit_2d_gaussian(psf_coeffs[0,:,:])
        #print gauss_psf_prior


    if return_postage_stamps:
        for k in range(n_stars):
            stellar_flux[k], sky_level[k] = fit_star_params(
                psf_coeffs,
                star_x[k], star_y[k],
                ps_exposure[k], ps_weight[k],
                ps_mask[k], ccd_shape,
                sky_sigma=0.05,
                stellar_flux_mean=stellar_flux_mean[k],
                stellar_flux_sigma=stellar_flux_sigma[k]
            )

        star_dict = {
            'ps_exposure':  ps_exposure,
            'ps_weight':    ps_weight,
            'ps_mask':      ps_mask,
            'star_x':       star_x,
            'star_y':       star_y,
            'star_ps1_mag': star_ps1_mag,
            'stellar_flux': stellar_flux,
            'sky_level':    sky_level
        }

        return psf_coeffs, star_dict

    return psf_coeffs


def load_exposure(fname_pattern, ccd_id):
    '''
    Load one CCD from an exposure.

    Inputs:
      fname_pattern  A filename of the form c4d_150109_051822_oo{}_z_v1.fits.fz,
                     where {} will be expanded in order to select the image,
                     weight and mask files.
      ccd_id         The identifier of the desired CCD (e.g., 'S31').

    Outputs:
      img_data     Exposure image
      weight_data  Weight image
      mask_data    Mask image
      wcs          The WCS astrometric solution
    '''

    img_data, img_header = astropy.io.fits.getdata(fname_pattern.format('i'),
                                                   ccd_id, header=True)
    wcs = astropy.wcs.WCS(header=img_header)

    weight_data = astropy.io.fits.getdata(fname_pattern.format('w'), ccd_id)
    mask_data = astropy.io.fits.getdata(fname_pattern.format('d'), ccd_id)

    # Apply the mask to the weights (and zero out the corresponding image pixels)
    #mask_idx = (mask_data != 0)
    #img_data[mask_idx] = 0.
    #weight_data[mask_idx] = 0.

    return img_data, weight_data, mask_data, wcs

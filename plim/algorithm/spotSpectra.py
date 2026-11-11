'''
class for calculating spot spectra from 3D spectral cube
'''
#%%


import logging
import numpy as np
from skimage.transform import rotate
from spectralCamera.algorithm.spotSpectraSimple import SpotSpectraSimple
from scipy.ndimage import gaussian_filter
from scipy.ndimage import shift as ndShift

logger = logging.getLogger(__name__)

class SpotSpectra(SpotSpectraSimple):
    ''' class for calculating spot spectra '''

    maskType = {'circle','square','offCentre'}
    
    DEFAULT = {'circle': True, # circle or square
                'pxBcg': 3, # thickness of the background shell
                'pxAve': 3, # radius of the spot
                'ratio': 1, # radio between the major and minor axis of the spot
                'angle': 0, # [deg] angle of the major axis from horizontal line
                'pxSpace': 1,  # space between spot and background
                'darkCount': 0, # offset in the signal, which should be subtracted
                'spectraSigma': 0, # sigma for gaussian filter in spectral axis
                'concentric': True # if true, signal and background are concentric, 
                                   # otherwise next to each other
                } 


    def __init__(self,image=None,spotPosition= [], wavelength = None, **kwarg):
        ''' initialization of the parameters '''

        super().__init__(image=image,spotPosition= spotPosition,
                         wavelength = wavelength, **kwarg)

        # parameters of the mask
        self.circle= kwarg['circle'] if 'circle' in kwarg else  self.DEFAULT['circle']
        self.ratio= kwarg['ratio'] if 'ratio' in kwarg else  self.DEFAULT['ratio']
        self.angle= kwarg['angle'] if 'angle' in kwarg else  self.DEFAULT['angle']
        self.pxBcg= int(kwarg['pxBcg']) if 'pxBcg' in kwarg else  self.DEFAULT['pxBcg']
        self.pxAve= int(kwarg['pxAve']) if 'pxAve' in kwarg else  self.DEFAULT['pxAve']
        self.pxSpace= int(kwarg['pxSpace']) if 'pxSpace' in kwarg else  self.DEFAULT['pxSpace']

        self.darkCount= kwarg['darkCount'] if 'darkCount' in kwarg else  self.DEFAULT['darkCount']
        self.spectraSigma= kwarg['spectraSigma'] if 'spectraSigma' in kwarg else  self.DEFAULT['spectraSigma']
        self.concentric= kwarg['concentric'] if 'concentric' in kwarg else  self.DEFAULT['concentric']

        self.maskBcg = None # weight for calculation of background spectra
        self.maskBcgIdx = None # indexes of of the mask

        # band dependent fractional mask (mosaic filter cameras, e.g. photonfocus)
        # each band image samples the scene with a sub-pixel offset [dy, dx];
        # the spot/background mask is shifted accordingly for each band
        self.bandOffset = kwarg['bandOffset'] if 'bandOffset' in kwarg else None # (nBand, 2) [px], None = standard mask
        self.maskSpotW = None # (nBand, ny, nx) normalised weights of the spot
        self.maskBcgW = None # (nBand, ny, nx) normalised weights of the background
        self.patchSpotIdx = None # (nSpot, ny, nx) image indexes of the patch around the spots
        self.patchBcgIdx = None # (nSpot, ny, nx) image indexes of the patch for the background
        self._bandMaskOffset = None # bandOffset, for which the weights were calculated

        self.maskImage = None # for visualisation
        self.outliers = None # bool vector with spotPosition, which are outside the image

        self.spectraRawSpot = []
        self.spectraRawBcg = []

        SpotSpectra.setMask(self)

    def setBandOffset(self, bandOffset):
        ''' set sub-pixel offset [dy, dx] of each band image (nBand, 2) in pixels
        None ... standard mask (the same for all bands) '''
        self.bandOffset = None if bandOffset is None else np.asarray(bandOffset, dtype=float)
        self.setMask()

    def _setBandMask(self):
        ''' calculate the band dependent fractional masks
        weight of a pixel = binary mask shifted (bilinear) by the band offset,
        i.e. the fraction of the shifted pixel cell inside the mask
        (for zero offset identical to the standard mask) '''

        self._bandMaskOffset = self.bandOffset
        self.patchSpotIdx = self.patchBcgIdx = None
        if self.bandOffset is None:
            self.maskSpotW = self.maskBcgW = None
            return

        # shifted masks, padded so that the shift stays inside
        pad = int(np.ceil(np.abs(self.bandOffset).max())) + 1
        spot = np.pad((self.maskSpot != 0).astype(float), pad)
        bcg = np.pad((self.maskBcg != 0).astype(float), pad)
        # value at x is taken from the mask at x + offset
        maskSpotW = np.array([ndShift(spot, -d, order=1) for d in self.bandOffset])
        maskBcgW = np.array([ndShift(bcg, -d, order=1) for d in self.bandOffset])

        # crop to the area with non-zero weights
        nz = np.any(maskSpotW > 0, axis=0) | np.any(maskBcgW > 0, axis=0)
        rows, cols = np.where(nz.any(axis=1))[0], np.where(nz.any(axis=0))[0]
        rs, cs = slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1)
        maskSpotW, maskBcgW = maskSpotW[:, rs, cs], maskBcgW[:, rs, cs]
        self.maskSpotW = maskSpotW / maskSpotW.sum(axis=(1, 2), keepdims=True)
        self.maskBcgW = maskBcgW / maskBcgW.sum(axis=(1, 2), keepdims=True)

        # pixel offsets of the patch relative to the spot position
        centre = spot.shape[0] // 2
        self._patchOffset = (np.arange(rows[0], rows[-1] + 1) - centre,
                             np.arange(cols[0], cols[-1] + 1) - centre)

    def _setPatchIdx(self, spotPosition):
        ''' image indexes of the patches around the spots (for the fractional mask)'''
        if self.maskSpotW is None:
            self.patchSpotIdx = self.patchBcgIdx = None
            return
        oy, ox = self._patchOffset
        self.patchSpotIdx = (spotPosition[:, 0, None, None] + oy[None, :, None],
                             spotPosition[:, 1, None, None] + ox[None, None, :])
        if self.concentric:
            self.patchBcgIdx = self.patchSpotIdx
        else:
            # background for all spots from the first one
            self.patchBcgIdx = (np.broadcast_to(self.patchSpotIdx[0][:1], self.patchSpotIdx[0].shape),
                                np.broadcast_to(self.patchSpotIdx[1][:1], self.patchSpotIdx[1].shape))

    def setMask(self,pxAve=None,pxBcg= None, pxSpace = None, 
                circle= None, ratio = None, angle = None, concentric = None):
        ''' set the geometry of spots and bcg mask 
            this function is overwritten 
        '''

        if pxAve is not None:
            self.pxAve = int(pxAve)
        if pxBcg is not None:
            self.pxBcg = int(pxBcg)
        if pxSpace is not None:
            self.pxSpace = int(pxSpace)
        if circle is not None:
            self.circle = circle
        if ratio is not None:
            self.ratio = ratio
        if angle is not None:
            self.angle = angle
        if concentric is not None:
            self.concentric = concentric

        # concentric mask
        if self.concentric:
            # mask has a spherical shape        
            if self.circle:
                self.maskSize = int(2*(self.pxBcg + self.pxAve + self.pxSpace) + 1 )

                xx, yy = np.meshgrid(np.arange(self.maskSize) - self.maskSize//2, (np.arange(self.maskSize) - self.maskSize//2))
                maskR = np.sqrt(xx**2 + yy**2)

                self.maskSpot = maskR<self.pxAve
                self.maskBcg = (maskR>(self.pxAve+self.pxSpace)) & (maskR<self.pxAve+self.pxSpace + self.pxBcg)
                
            # mask has a squares
            else:
                a = (self.pxBcg + self.pxAve + self.pxSpace)
                b = (self.pxBcg + self.pxAve*self.ratio + self.pxSpace)
                self.maskSize = 2*int(np.sqrt(a**2 + b**2)) +1

                xx, yy = np.meshgrid(np.arange(self.maskSize) - self.maskSize//2, (np.arange(self.maskSize) - self.maskSize//2))

                self.maskSpot = (np.abs(xx)<self.pxAve) & (np.abs(yy)<self.pxAve*self.ratio)
                self.maskBcg = ((~(
                                    (np.abs(xx)<(self.pxAve+self.pxSpace)) & 
                                    (np.abs(yy)<(self.pxAve*self.ratio+self.pxSpace))
                                )) &
                                (
                                    (np.abs(xx)<(self.pxAve+self.pxSpace + self.pxBcg)) &
                                    (np.abs(yy)<(self.pxAve*self.ratio+self.pxSpace + self.pxBcg))
                                ))

                self.maskSpot = rotate(self.maskSpot,self.angle)
                self.maskBcg = rotate(self.maskBcg,self.angle)
        else:
            # define spherical mask,
            # the background for all spots will be taken from the first spot
            self.maskSize = int(2*np.max((self.pxBcg,self.pxAve)) + 1 )

            xx, yy = np.meshgrid(np.arange(self.maskSize) - self.maskSize//2, (np.arange(self.maskSize) - self.maskSize//2))
            maskR = np.sqrt(xx**2 + yy**2)

            self.maskSpot = maskR<self.pxAve
            self.maskBcg = maskR<self.pxBcg

        # band dependent fractional masks
        self._setBandMask()

        # return if there is no image
        if not hasattr(self,'image'):
            return
        else:
            self.maskImage = 0*self.image[0,:,:]

        # identify the spots, whose mask is not whole in image
        # convert self.spotPosition to numpy array. it is better to operate on
        _spotPosition = np.array(self.spotPosition, dtype=int)

        if _spotPosition.size ==0:
            self.spectraSpot = []
            self.spectraRawSpot = []
            self.spectraRawBcg = []
            return

        # define the bool vector with outliers
        self.outliers = np.zeros(_spotPosition.shape[0], dtype=bool)

        try:
            # get the indexes of the masks and bcgMask
            _maskSpotIdx = np.where(self.maskSpot)
            _maskBcgIdx = np.where(self.maskBcg)

            self.maskSpotIdx = (
            _maskSpotIdx[0]+ _spotPosition[:,0][:,None]-self.maskSize//2,
            _maskSpotIdx[1]+ _spotPosition[:,1][:,None]-self.maskSize//2
            )
            self.maskBcgIdx = (
            _maskBcgIdx[0]+ _spotPosition[:,0][:,None]-self.maskSize//2,
            _maskBcgIdx[1]+ _spotPosition[:,1][:,None]-self.maskSize//2
            )
            
            # set backgrounds mask for all spots to the first one 
            if self.concentric== False:
                self.maskBcgIdx[0][:,:] = self.maskBcgIdx[0][0,:]
                self.maskBcgIdx[1][:,:] = self.maskBcgIdx[1][0,:]

            _olm = np.any((
                self.maskSpotIdx[0]<0, 
                self.maskSpotIdx[0]>self.maskImage.shape[0]-1, 
                self.maskSpotIdx[1]<0,
                self.maskSpotIdx[1]>self.maskImage.shape[1]-1,
                ),axis=0)
            _olb = np.any((
                self.maskBcgIdx[0]<0, 
                self.maskBcgIdx[0]>self.maskImage.shape[0]-1, 
                self.maskBcgIdx[1]<0,
                self.maskBcgIdx[1]>self.maskImage.shape[1]-1,
                ),axis=0)

            self.outliers = np.any([np.any(_olm,axis=1), np.any(_olb,axis=1)], axis=0)

            # patches for the fractional mask (slightly larger than the mask)
            self._setPatchIdx(_spotPosition)
            if self.patchSpotIdx is not None:
                for _idx in (self.patchSpotIdx, self.patchBcgIdx):
                    self.outliers |= np.any((
                        _idx[0].min(axis=(1,2))<0,
                        _idx[0].max(axis=(1,2))>self.maskImage.shape[0]-1,
                        _idx[1].min(axis=(1,2))<0,
                        _idx[1].max(axis=(1,2))>self.maskImage.shape[1]-1,
                        ),axis=0)

            # set mask to one
            self.maskImage[self.maskSpotIdx[0][~self.outliers,:],
                        self.maskSpotIdx[1][~self.outliers,:]] = 1
            
            # set bcg to two
            self.maskImage[self.maskBcgIdx[0][~self.outliers,:],
                        self.maskBcgIdx[1][~self.outliers,:]] = 2
            
        except:
            logger.exception('error in setting mask')



    def calculateSpectra(self):
        ''' calculate the spectra
         this function is overwritten
        '''

        if self.spotPosition is None or len(self.spotPosition)==0:
            self.spectraSpot = []
            self.spectraRawSpot = []
            self.spectraRawBcg = []
            return
        else:
            nSpot = len(self.spotPosition)
        
        if (self.maskSpotIdx is None) or (self.maskBcgIdx is None):
            return
        
        if not hasattr(self,'image') or self.image is None:
            return

        # bandOffset was set directly (not by setBandOffset) - update the masks
        if self._bandMaskOffset is not self.bandOffset:
            self.setMask()

        _spectraRawSpot = np.ones((nSpot,self.image.shape[0]))
        _spectraRawBcg = np.ones((nSpot,self.image.shape[0]))

        # band dependent fractional mask
        useBandMask = self.patchSpotIdx is not None
        if useBandMask and self.maskSpotW.shape[0] != self.image.shape[0]:
            logger.warning(f'number of band offsets ({self.maskSpotW.shape[0]}) is not equal '
                           f'to image spectral channels ({self.image.shape[0]}) - standard mask used')
            useBandMask = False

        try:
            if useBandMask:
                # weighted sum over the patch around each spot, own weights per band
                ok = ~self.outliers
                _patch = self.image[:, self.patchSpotIdx[0][ok], self.patchSpotIdx[1][ok]]
                _spectraRawSpot[ok,:] = np.einsum('wsij,wij->sw', _patch, self.maskSpotW)
                if self.patchBcgIdx is not self.patchSpotIdx:
                    _patch = self.image[:, self.patchBcgIdx[0][ok], self.patchBcgIdx[1][ok]]
                _spectraRawBcg[ok,:] = np.einsum('wsij,wij->sw', _patch, self.maskBcgW)
            else:
                _spectraRawSpot[~self.outliers,:] = np.sum(
                    self.image[:,
                                self.maskSpotIdx[0][~self.outliers,:],
                                self.maskSpotIdx[1][~self.outliers,:]
                                ],axis=2).T
                _spectraRawSpot[~self.outliers,:] = (
                    _spectraRawSpot[~self.outliers,:] / self.maskSpotIdx[0].shape[1]
                )

                _spectraRawBcg[~self.outliers,:] = np.sum(
                    self.image[:,
                                self.maskBcgIdx[0][~self.outliers,:],
                                self.maskBcgIdx[1][~self.outliers,:]
                                ],axis=2).T
                _spectraRawBcg[~self.outliers,:] = (
                     _spectraRawBcg[~self.outliers,:] / self.maskBcgIdx[0].shape[1]
                )

        except:
            logger.exception('error in calculateSpectra')


        # apply spectral smoothing and background substration
        _spectraRawBcg = gaussian_filter(_spectraRawBcg, sigma=self.spectraSigma, axes=1)
        _spectraRawSpot = gaussian_filter(_spectraRawSpot, sigma=self.spectraSigma, axes=1)
        _spectraRawBcg -= self.darkCount
        _spectraRawSpot -= self.darkCount

        # if not concentric then set background-point spectrum equal to one
        if not self.concentric:
            _spectraRawSpot[0] = _spectraRawBcg[0]

        # calculate the spectra
        _spectraSpot = _spectraRawSpot/_spectraRawBcg

        self.spectraRawSpot = _spectraRawSpot.tolist()
        self.spectraRawBcg = _spectraRawBcg.tolist()
        self.spectraSpot = _spectraSpot.tolist()

    def getA(self):
        ''' return absorption spectra of the spots '''
        return (1 - np.array(self.spectraSpot)).tolist()

#%%

if __name__ == "__main__":
    pass
















# %%

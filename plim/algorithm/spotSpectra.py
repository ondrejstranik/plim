'''
class for calculating spot spectra from 3D spectral cube
'''
#%%


import numpy as np
from skimage.transform import rotate
import traceback
from spectralCamera.algorithm.spotSpectraSimple import SpotSpectraSimple


class SpotSpectra(SpotSpectraSimple):
    ''' class for calculating spot spectra '''
    
    maskType = {'circle','square','offCentre'}
    
    DEFAULT = {'circle': True, # circle or square
                'pxBcg': 3, # thickness of the background shell
                'pxAve': 3, # radius of the spot
                'ratio': 1, # radio between the major and minor axis of the spot
                'angle': 0, # [deg] angle of the major axis from horizontal line
                'pxSpace': 1,  # space between spot and background
                'darkCount': 0} # offset in the signal, which should be subtracted


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

        self.maskBcg = None # weight for calculation of background spectra
        self.maskBcgIdx = None # indexes of of the mask

        self.maskImage = None # for visualisation
        self.outliers = None # bool vector with spotPosition, which are outside the image

        self.spectraRawSpot = []
        self.spectraRawBcg = []

        SpotSpectra.setMask(self)
        
    def setMask(self,pxAve=None,pxBcg= None, pxSpace = None, 
                circle= None, ratio = None, angle = None):
        ''' set the geometry of spots and bcg mask  and calculate spectra
        this function is rewritten 
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

            '''
            # mask has a squares with off set
            self.maskSize = int(2*self.pxAve + self.pxSpace)
            xx, yy = np.meshgrid(np.arange(self.maskSize) - self.maskSize//2,
                                 np.arange(self.maskSize) - self.maskSize//2)

            self.maskSpot = (xx<-self.pxSpace/2) & (np.abs(yy)<self.pxAve/2)
            self.maskBcg = (xx> self.pxSpace/2) & (np.abs(yy)<self.pxAve/2)

            self.maskSpot = rotate(self.maskSpot,self.angle)
            self.maskBcg = rotate(self.maskBcg,self.angle)
            '''

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

            # set mask to one
            self.maskImage[self.maskSpotIdx[0][~self.outliers,:],
                        self.maskSpotIdx[1][~self.outliers,:]] = 1
            
            # set bcg to two
            self.maskImage[self.maskBcgIdx[0][~self.outliers,:],
                        self.maskBcgIdx[1][~self.outliers,:]] = 2
            
        except:
            print('error in setting mask')
            traceback.print_exc()

        # calculate the spectra with the new mask
        self.calculateSpectra()


    def calculateSpectra(self):
        ''' calculate the spectra
         this function is rewritten
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

        _spectraRawSpot = np.ones((nSpot,self.image.shape[0]))
        _spectraRawBcg = np.ones((nSpot,self.image.shape[0]))

        try:
            _spectraRawSpot[~self.outliers,:] = np.sum(
                self.image[:,
                            self.maskSpotIdx[0][~self.outliers,:],
                            self.maskSpotIdx[1][~self.outliers,:]
                            ],axis=2).T

            _spectraRawBcg[~self.outliers,:] = np.sum(
                self.image[:,
                            self.maskBcgIdx[0][~self.outliers,:],
                            self.maskBcgIdx[1][~self.outliers,:]
                            ],axis=2).T
        except:
            print('error in calculateSpectra')
            traceback.print_exc()


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

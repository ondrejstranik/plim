'''
class for calculating spot spectra from 3D spectral cube
'''
#%%


import numpy as np


class SpotSpectra:
    ''' class for calculating spot spectra '''
    DEFAULT = {'pxBcg': 3, # thickness of the background shell
                'pxAve': 3, # radius of the spot
                'pxSpace': 1} # space between spot and background


    def __init__(self,wxyImage=None,spotPosition= [],**kwarg):
        ''' initialization of the parameters '''

        if wxyImage is not None: self.wxyImage = wxyImage  # spectral Image
        if spotPosition is not []: self.spotPosition = spotPosition

        # parameters of the mask
        self.pxBcg= int(kwarg['pxBcg']) if 'pxBcg' in kwarg else  self.DEFAULT['pxBcg']
        self.pxAve= int(kwarg['pxAve']) if 'pxAve' in kwarg else  self.DEFAULT['pxAve']
        self.pxSpace= int(kwarg['pxSpace']) if 'pxSpace' in kwarg else  self.DEFAULT['pxSpace']

        self.maskSize = None # total size of the mask
        self.maskSpot = None # weights for calculation of spots spectra
        self.maskBcg = None # weight for calculation of background spectra
        self.maskImage = None # for visualisation only
 
        self.spectraRawSpot = []
        self.spectraRawBcg = []
        self.spectraSpot = []

        self.setMask()
        
        self.calculateSpectra()

    def setMask(self,pxAve=None,pxBcg= None, pxSpace = None):
        ''' set the geometry of spots and bcg mask  and calculate spectra'''

        if pxAve is not None:
            self.pxAve = int(pxAve)
        if pxBcg is not None:
            self.pxBcg = int(pxBcg)
        if pxSpace is not None:
            self.pxSpace = int(pxSpace)
        self.maskSize = int(2*(self.pxBcg + self.pxAve + self.pxSpace) + 1 )

        xx, yy = np.meshgrid(np.arange(self.maskSize) - self.maskSize//2, (np.arange(self.maskSize) - self.maskSize//2))
        maskR = np.sqrt(xx**2 + yy**2)

        self.maskSpot = maskR<self.pxAve
        self.maskBcg = (maskR>(self.pxAve+self.pxSpace)) & (maskR<self.pxAve+self.pxSpace + self.pxBcg)
        
        # set mask image (for visualisation only)
        if hasattr(self,'wxyImage'):
            self.maskImage = 0*self.wxyImage[0,:,:]
            for myspot in self.spotPosition:
                try:
                    self.maskImage[int(myspot[0])-self.maskSize//2:int(myspot[0])+self.maskSize//2+1,
                                    int(myspot[1])-self.maskSize//2:int(myspot[1])+self.maskSize//2+1] = \
                                    self.maskSpot*2
                    self.maskImage[int(myspot[0])-self.maskSize//2:int(myspot[0])+self.maskSize//2+1,
                                    int(myspot[1])-self.maskSize//2:int(myspot[1])+self.maskSize//2+1] += \
                                    self.maskBcg*1
                except:
                    pass

        self.calculateSpectra()

    def setSpot(self, spotPosition):
        ''' set position of the spots  and calculate spectra'''
        self.spotPosition = spotPosition

        self.setMask()
        #self.calculateSpectra()

    def setImage(self, wxyImage):
        ''' set the spectra image and calculate image and calculate spectra'''
        self.wxyImage = wxyImage

        self.calculateSpectra()

    def calculateSpectra(self):
        ''' calculate the spectra '''

        self.spectraRawSpot = []
        self.spectraRawBcg = []
        self.spectraSpot = []

        maskSpotFlatten = self.maskSpot.flatten()
        maskBcgFlatten = self.maskBcg.flatten()

        for myspot in self.spotPosition:
            # image of the single spots with surrounding 
            myAreaImage = self.wxyImage[:,int(myspot[0])-self.maskSize//2:int(myspot[0])+self.maskSize//2+1,
                            int(myspot[1])-self.maskSize//2:int(myspot[1])+self.maskSize//2+1]
            myAreaImageFlatten = myAreaImage.reshape(myAreaImage.shape[0],-1)

            try:
                spectraRawSpot = np.mean(myAreaImageFlatten[:,maskSpotFlatten], axis=1)
                spectraRawBcg = np.mean(myAreaImageFlatten[:,maskBcgFlatten], axis=1)
            except:
                spectraRawSpot = np.ones(self.wxyImage.shape[0])
                spectraRawBcg = np.ones(self.wxyImage.shape[0])

            spectraSpot = spectraRawSpot/spectraRawBcg

            self.spectraRawSpot.append(spectraRawSpot)        
            self.spectraRawBcg.append(spectraRawBcg)        
            self.spectraSpot.append(spectraSpot)  


    def getMask(self):
        ''' return the image of the mask of spots and background '''
        return self.maskImage

    def getT(self):
        ''' return transmission spectra of the spots '''
        return self.spectraSpot

    def getA(self):
        ''' return absorption spectra of the spots '''
        return (1 - np.array(self.spectraSpot)).tolist()

#%%

if __name__ == "__main__":
    pass
















# %%

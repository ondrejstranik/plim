'''
class for calculating spot spectra from 3D spectral cube
'''
#%%


import numpy as np
from skimage.transform import rotate


class SpotSpectra:
    ''' class for calculating spot spectra '''
    
    maskType = {'circle','square','offCentre'}
    
    DEFAULT = {'circle': True, # circle or square
                'pxBcg': 3, # thickness of the background shell
                'pxAve': 3, # radius of the spot
                'ratio': 1, # radio between the major and minor axis of the spot
                'angle': 0, # [deg] angle of the major axis from horizontal line
                'pxSpace': 1,  # space between spot and background
                'darkCount': 0} # offset in the signal, which should be subtracted


    def __init__(self,wxyImage=None,spotPosition= [],**kwarg):
        ''' initialization of the parameters '''

        if wxyImage is not None: self.wxyImage = wxyImage  # spectral Image
        if spotPosition is not []: self.spotPosition = spotPosition

        # parameters of the mask
        self.circle= kwarg['circle'] if 'circle' in kwarg else  self.DEFAULT['circle']
        self.ratio= kwarg['ratio'] if 'ratio' in kwarg else  self.DEFAULT['ratio']
        self.angle= kwarg['angle'] if 'angle' in kwarg else  self.DEFAULT['angle']
        self.pxBcg= int(kwarg['pxBcg']) if 'pxBcg' in kwarg else  self.DEFAULT['pxBcg']
        self.pxAve= int(kwarg['pxAve']) if 'pxAve' in kwarg else  self.DEFAULT['pxAve']
        self.pxSpace= int(kwarg['pxSpace']) if 'pxSpace' in kwarg else  self.DEFAULT['pxSpace']

        self.darkCount= kwarg['darkCount'] if 'darkCount' in kwarg else  self.DEFAULT['darkCount']


        self.maskSize = None # total size of the mask
        self.maskSpot = None # weights for calculation of spots spectra
        self.maskBcg = None # weight for calculation of background spectra
        self.maskImage = None # for visualisation only
 
        self.spectraRawSpot = []
        self.spectraRawBcg = []
        self.spectraSpot = []

        self.setMask()
        
        #self.calculateSpectra()

    def setMask(self,pxAve=None,pxBcg= None, pxSpace = None, 
                circle= None, ratio = None, angle = None):
        ''' set the geometry of spots and bcg mask  and calculate spectra'''

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
            

        else:
            '''
            # mask has a squares
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

            #print(f'maskSpot \n  {self.maskSpot}')
            #print(f'maskBcg \n  {self.maskSpot}')


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
                    print('error in setting self.maskImage')
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

            try:

                myAreaImage = self.wxyImage[:,int(myspot[0])-self.maskSize//2:int(myspot[0])+self.maskSize//2+1,
                                int(myspot[1])-self.maskSize//2:int(myspot[1])+self.maskSize//2+1]
                myAreaImageFlatten = myAreaImage.reshape(myAreaImage.shape[0],-1)


                spectraRawSpot = np.mean(myAreaImageFlatten[:,maskSpotFlatten], axis=1)
                spectraRawBcg = np.mean(myAreaImageFlatten[:,maskBcgFlatten], axis=1)

                spectraRawSpot = spectraRawSpot - self.darkCount
                spectraRawBcg  = spectraRawBcg -  self.darkCount

                spectraRawSpot[spectraRawSpot <=1] = 1 # avoid small numbers and negative
                spectraRawBcg[spectraRawBcg <=1] = 1 # avoid division by small numbers and negative 

                spectraSpot = spectraRawSpot/spectraRawBcg

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

"""
class to generate virtual sample

@author: ostranik
"""
#%%

import numpy as np
from skimage import data
from skimage.transform import resize
from spectralCamera.virtualSystem.component.sample2 import Sample2
from skimage.draw import disk
from timeit import default_timer as timer


class Sample3(Sample2):
    ''' class to define a sample object of the microscope'''
    DEFAULT = {'deltaTime': 60, #[s]
                'deltaShift': 10, # [nm]
                'deltaVolume':30 # ul/min
    } 
    
    def __init__(self,*args, **kwargs):
        ''' initialisation '''
        super().__init__(*args, **kwargs)

        self.time0 = timer()

    def setPlasmonArray(self,samplePixelSize=None,
                        samplePosition = None,
                        arraySize= None,
                        spotDiameter = None, 
                        wavelength  = None,
                        plasmonPeak = None,
                        plasmonSigma = None,
                        absorbanceMax =  None
                        ):

        DEFAULT = { 'samplePixelSize':1, # um
                    'samplePosition': np.array([10,10,0]),  # pixels
                    'arraySize': np.array([5,10]),
                    'spotDiameter': 5,  # pixels
                    'wavelength': np.arange(400,800,10),
                    'plasmonPeak': 550, # nm
                    'plasmonSigma' : 40, # nm
                    'absorbanceMax': 0.5 } # absorbance of the plasmon peak 

        self.position=DEFAULT['samplePosition'] if samplePosition is None else samplePosition
        self.pixelSize=DEFAULT['samplePixelSize'] if samplePixelSize is None else samplePixelSize

        self.wavelength = DEFAULT['wavelength'] if wavelength is None else wavelength
        
        self.peak = DEFAULT['plasmonPeak'] if plasmonPeak is None else plasmonPeak       
        self.sigma = DEFAULT['plasmonSigma'] if plasmonSigma is None else plasmonSigma
        self.aMax=DEFAULT['absorbanceMax'] if absorbanceMax is None else absorbanceMax 

        aSize=DEFAULT['arraySize'] if arraySize is None else arraySize
        diameter=DEFAULT['spotDiameter'] if spotDiameter is None else spotDiameter

        size = aSize*4*diameter
        _sample = np.zeros((self.wavelength.shape[0],*size))

        xIdx, yIdx = np.meshgrid(np.arange(aSize[1]), np.arange(aSize[0]))
        positionIdx = np.array([yIdx.ravel(),xIdx.ravel()]).T


        # set the value in the samples

        self.rrList = []
        self.ccList = []
        self.peakList = []
        
        for ii in range(np.prod(aSize)):
            _disk = np.array([diameter + 4*positionIdx[ii,0]*diameter, diameter+ 4*positionIdx[ii,1]*diameter, diameter])

            # add small variation
            _disk[0] += np.random.rand(1)*2 - 1
            _disk[1] += np.random.rand(1)*2 - 1
            _disk[2] += (np.random.rand(1)*2 - 1 )*0.1*_disk[2]
            _peak = self.peak + (np.random.rand(1)*2-1)*10

            rr, cc = disk((_disk[0],_disk[1]), _disk[2], shape=_sample.shape[1:])
            # gauss peak
            _sample[:,rr,cc] = self.aMax*np.exp(-(self.wavelength-_peak)**2/2/self.sigma**2)[:,None]
            # sigmoid + constant offset
            _sample[:,rr,cc] += self.aMax/4/(1 + np.exp((self.wavelength-_peak)/self.sigma))[:,None] + self.aMax/10
            
            self.rrList.append(rr)
            self.ccList.append(cc)
            self.peakList.append(_peak)

        self.data = _sample

    def setPlasmonShift(self,shift, spot=None):
        ''' set the plasmon shift in the array of spots
        shift .. array of the relative shifts [nm]
        spot .. indexes of the spots, which should be shifted
                == 1/2 half of the spots are shifted'''

        
        if spot == 1/2:
            spot= np.arange(0,len(self.rrList),2)

        spot= np.array(spot) if spot is not None else np.arange(len(self.rrList))

        shift = np.array([shift]) if isinstance(shift, (int,float)) else np.array(shift)
        if len(shift) != len(spot): shift = np.ones_like(spot)*shift

        for ii,idx  in enumerate(spot):
            self.data[:,self.rrList[idx],self.ccList[idx]] = (
            # gauss peak 
            self.aMax*np.exp(-(self.wavelength-self.peakList[idx]-shift[ii])**2/2/self.sigma**2)[:,None] + 
            # sigmoid 
            self.aMax/4/(1 + np.exp((self.wavelength-self.peakList[idx]-shift[ii])/self.sigma))[:,None] + 
            # constant offset
            self.aMax/10)

        #print(f'new plasmonShift: {shift} nm')


    def getActualShift(self, totalFlow= None):
        ''' stepwise varies the refractive index 
         if totalFlow is None then it varies temporary
         else depends on the volume of the totalFlow'''
        
        if totalFlow is None:
            timeNow = timer()
            return Sample3.DEFAULT['deltaShift']*round((timeNow -self.time0)%Sample3.DEFAULT['deltaTime']/Sample3.DEFAULT['deltaTime'])
        else:
            return Sample3.DEFAULT['deltaShift']*round((totalFlow)%Sample3.DEFAULT['deltaVolume']/Sample3.DEFAULT['deltaVolume'])








#%%

if __name__ == '__main__':
    pass


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


class Sample3(Sample2):
    ''' class to define a sample object of the microscope'''
    DEFAULT = {}
    
    def __init__(self,*args, **kwargs):
        ''' initialisation '''
        super().__init__(*args, **kwargs)

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
                    'samplePosition': np.array([0,0,0]),  # pixels
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

        aSize=DEFAULT['arraySize'] if arraySize is None else arraySize
        diameter=DEFAULT['spotDiameter'] if spotDiameter is None else spotDiameter
        aMax=DEFAULT['absorbanceMax'] if absorbanceMax is None else absorbanceMax   

        size = aSize*4*diameter
        _sample = np.zeros((self.wavelength.shape[0],*size))

        xIdx, yIdx = np.meshgrid(np.arange(aSize[1]), np.arange(aSize[0]))
        positionIdx = np.array([yIdx.ravel(),xIdx.ravel()]).T


        for ii in range(np.prod(aSize)):
            _disk = np.array([diameter + 4*positionIdx[ii,0]*diameter, diameter+ 4*positionIdx[ii,1]*diameter, diameter])

            # add small variation
            _disk[0] += np.random.rand(1)*2 - 1
            _disk[1] += np.random.rand(1)*2 - 1
            _disk[2] += (np.random.rand(1)*2 - 1 )*0.1*_disk[2]
            _peak = self.peak + (np.random.rand(1)*2-1)*10

            rr, cc = disk((_disk[0],_disk[1]), _disk[2], shape=_sample.shape[1:])
            # gauss peak
            _sample[:,rr,cc] = aMax*np.exp(-(self.wavelength-_peak)**2/2/self.sigma**2)[:,None]
            # heviside + constant offset
            _sample[:,rr,cc] += aMax/4/(1 + np.exp(self.wavelength-_peak))[:,None] + aMax/10


        self.data = _sample



#%%

if __name__ == '__main__':
    pass


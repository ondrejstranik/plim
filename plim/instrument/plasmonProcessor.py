"""
plasmon processor - process the spectral images

Created on Mon Nov 15 12:08:51 2021

@author: ostranik
"""
#%%

import os
import time
import numpy as np
from viscope.instrument.base.baseProcessor import BaseProcessor
from plim.algorithm.plasmonFit import PlasmonFit
from plim.algorithm.spotSpectra import SpotSpectra


class PlasmonProcessor(BaseProcessor):
    ''' class to control processing of spectral images to get plasmon signals'''
    DEFAULT = {'name': 'PlasmonProcessor'}

    def __init__(self, name=None, **kwargs):
        ''' initialisation '''

        if name== None: name= PlasmonProcessor.DEFAULT['name']
        super().__init__(name=name, **kwargs)
        
        # spectral camera
        self.sCamera = None
        
        self.pF = None
        self.spotSpectra = None


    def connect(self,sCamera=None):
        ''' connect data processor with the camera '''
        if sCamera is not None:
            super().connect(sCamera.flagLoop)
            self.setParameter('sCamera',sCamera)
            self.pF = PlasmonFit(wavelength = sCamera.getParameter('wavelength'))
            self.spotSpectra = SpotSpectra(sCamera.sImage)

        else:
            super().connect()

    def setParameter(self,name, value):
        ''' set parameter of the spectral camera'''
        super().setParameter(name,value)

        if name== 'sCamera':
            self.sCamera = value
            self.flagToProcess = self.sCamera.flagLoop
            self.pF = PlasmonFit(wavelength = self.sCamera.getParameter('wavelength'))
            self.spotSpectra = SpotSpectra(self.sCamera.sImage)

    def getParameter(self,name):
        ''' get parameter of the camera '''
        _value = super().getParameter(name)
        if _value is not None: return _value        

        if name== 'sCamera':
            return self.sCamera

    def processData(self):
        ''' process newly arrived data '''
        print(f"processing data from {self.DEFAULT['name']}")
        self.spotSpectra.setImage(self.sCamera.sImage)
        self.pF.setSpectra(self.spotSpectra.getA())
        self.pF.setWavelength(self.sCamera.wavelength)
        self.pF.calculateFit()
        print(self.pF.wavelength)
        print(self.spotSpectra.getA())        


#%%

# TODO: test it!
if __name__ == '__main__':
    pass

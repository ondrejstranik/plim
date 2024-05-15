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
from plim.algorithm.spotData import SpotData


class PlasmonProcessor(BaseProcessor):
    ''' class to control processing of spectral images to get plasmon signals'''
    DEFAULT = {'name': 'PlasmonProcessor'}

    def __init__(self, name=None, **kwargs):
        ''' initialisation '''

        if name== None: name= PlasmonProcessor.DEFAULT['name']
        super().__init__(name=name, **kwargs)
        
        # spectral camera
        self.sCamera = None
        
        # data container
        self.pF = PlasmonFit()
        self.spotSpectra = SpotSpectra()
        self.spotData = SpotData()


    def connect(self,sCamera=None):
        ''' connect data processor with the camera '''
        super().connect()
        if sCamera is not None: self.setParameter('sCamera',sCamera)

    def setParameter(self,name, value):
        ''' set parameter of the spectral camera'''
        super().setParameter(name,value)

        if name== 'sCamera':
            self.sCamera = value
            self.flagToProcess = self.sCamera.flagLoop

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
        newSignal = self.pF.getPosition()
        if newSignal != []:
            self.spotData.addDataValue(newSignal,time.time())

        


#%%

# TODO: test it!
if __name__ == '__main__':
    pass

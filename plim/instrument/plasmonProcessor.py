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


class PlasmonProcessor(BaseProcessor):
    ''' class to control processing of spectral images to get plasmon signals'''
    DEFAULT = {'name': 'PlasmonProcessor'}

    def __init__(self, name=None, **kwargs):
        ''' initialisation '''

        if name== None: name= PlasmonProcessor.DEFAULT['name']
        super().__init__(name=name, **kwargs)
        
        # spectral camera
        self.sCamera = None
        
    def connect(self,sCamera=None):
        ''' connect data processor with the camera '''
        if sCamera is not None:
            super().connect(sCamera.flagLoop)
            self.setParameter('camera',camera)
        else:
            super().connect()

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

    #TODO: finish the class !!!
    def processData(self):
        ''' process newly arrived data '''
        print('processing data')
        self.sImage = self.imageDataToSpectralCube(self.camera.rawImage)
        return self.sImage


#%%

if __name__ == '__main__':
    pass

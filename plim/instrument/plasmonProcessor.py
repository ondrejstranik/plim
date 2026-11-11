"""
plasmon processor - process the spectral images

Created on Mon Nov 15 12:08:51 2021

@author: ostranik
"""
#%%

import os
import time
import logging
import numpy as np
from viscope.instrument.base.baseProcessor import BaseProcessor
from plim.algorithm.plasmonFit import PlasmonFit
from plim.algorithm.spotSpectra import SpotSpectra
from plim.algorithm.spotData import SpotData
from plim.algorithm.flowData import FlowData
from plim.algorithm.injectionData import InjectionData

logger = logging.getLogger(__name__)


class PlasmonProcessor(BaseProcessor):
    ''' class to control processing of spectral images to get plasmon signals
    and collect flow rates from a pump'''
    DEFAULT = {'name': 'PlasmonProcessor'
                }

    def __init__(self, name=None, **kwargs):
        ''' initialisation '''

        if name== None: name= PlasmonProcessor.DEFAULT['name']
        super().__init__(name=name, **kwargs)

        # sleep at least as long as the last processing took (max ~50 % load)
        # - keeps the GUI responsive with many spots and short exposure
        self.idleRatio = 1

        # spectral camera
        self.sCamera = None
        # spectral camera
        self.pump = None
        
        # data container
        self.pF = PlasmonFit()
        self.spotSpectra = SpotSpectra()
        self.spotData = SpotData()
        self.flowData = FlowData()
        self.injectionData = InjectionData()

        # wavelength (object) of the camera, for which the band offset was set
        self._bandOffsetWavelength = None


    def connect(self,sCamera=None,pump=None):
        ''' connect data processor with the camera, pump '''
        super().connect()
        if sCamera is not None: self.setParameter('sCamera',sCamera)
        if pump is not None: self.setParameter('pump',pump)

    def setParameter(self,name, value):
        ''' set parameter of the spectral camera'''
        super().setParameter(name,value)

        if name== 'sCamera':
            self.sCamera = value
            self.flagToProcess = self.sCamera.flagLoop
            self.setBandOffset()

        if name== 'pump':
            self.pump = value

    def getParameter(self,name):
        ''' get parameter of the camera '''
        _value = super().getParameter(name)
        if _value is not None: return _value        

        if name== 'sCamera':
            return self.sCamera

        if name== 'pump':
            return self.pump

    def setBandOffset(self):
        ''' set the sub-pixel offset of the band images from the spectral camera
        (band dependent fractional mask in spotSpectra), None if the camera does not provide it '''
        if self.sCamera is None: return
        self._bandOffsetWavelength = self.sCamera.wavelength
        getOffset = getattr(self.sCamera, 'getBandOffset', None)
        try:
            bandOffset = getOffset() if getOffset is not None else None
        except:
            logger.exception('could not get the band offset from the spectral camera')
            bandOffset = None
        logger.info(f'band offset of the spectral image: {"none" if bandOffset is None else "set"}')
        self.spotSpectra.setBandOffset(bandOffset)

    def processData(self):
        ''' process newly arrived data '''
        logger.debug(f"processing data from {self.DEFAULT['name']}")

        # new calibration / new folder of recorded images -> update the band offset
        if self.sCamera.wavelength is not self._bandOffsetWavelength:
            self.setBandOffset()

        # take the image and its acquisition time together - sCamera can
        # deliver a new image (and t0) while this frame is being processed
        sImage = self.sCamera.sImage
        newTime = self.sCamera.t0

        self.spotSpectra.setImage(sImage)
        self.spotSpectra.setWavelength(self.sCamera.wavelength)
        self.spotSpectra.calculateSpectra()
        self.pF.setSpectra(self.spotSpectra.getSpectra())
        self.pF.setWavelength(self.sCamera.wavelength)
        self.pF.calculateFit()
        newFlow = self.pump.getParameter('flowRateReal') if self.pump is not None else None 
        newSignal = self.pF.getPosition()
        if newSignal != []:
            t0 = self.spotData.addDataValue(newSignal,newTime)
            if t0 is not None: 
                self.flowData.clearData()
                self.flowData.setT0(t0)
                self.injectionData.setT0(t0)
        if newFlow is not None:
            self.flowData.addDataValue([newFlow],newTime)
    

#%%

if __name__ == '__main__':
    pass


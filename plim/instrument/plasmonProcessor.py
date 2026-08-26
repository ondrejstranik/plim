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

        # base loopDelay as last explicitly requested via setParameter() -
        # processData() adds to this (rather than overwriting it) once
        # there are spots to fit, so the user's requested base value is
        # never lost once the extra throttling kicks in or drops out again
        self._baseLoopDelay = self.loopDelay

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


    def connect(self,sCamera=None,pump=None):
        ''' connect data processor with the camera, pump '''
        super().connect()
        if sCamera is not None: self.setParameter('sCamera',sCamera)
        if pump is not None: self.setParameter('pump',pump)

    def setParameter(self,name, value):
        ''' set parameter of the spectral camera'''
        super().setParameter(name,value)

        if name== 'loopDelay':
            self._baseLoopDelay = value

        if name== 'sCamera':
            self.sCamera = value
            self.flagToProcess = self.sCamera.flagLoop

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

    def processData(self):
        ''' process newly arrived data '''
        logger.debug(f"processing data from {self.DEFAULT['name']}")

        # extra throttling once there are spots to fit - fitting is
        # noticeably heavier than idle polling with no spots yet, so slow
        # the loop down further to reduce GUI freezing. loopDelay is
        # re-read fresh by BaseProcessor.loop()'s time.sleep(self.loopDelay)
        # right after this method returns, so this takes effect immediately
        hasSpots = self.spotSpectra.spotPosition is not None and len(self.spotSpectra.spotPosition) > 0
        self.loopDelay = self._baseLoopDelay + 1 if hasSpots else self._baseLoopDelay

        self.spotSpectra.setImage(self.sCamera.sImage)
        self.spotSpectra.setWavelength(self.sCamera.wavelength)
        self.spotSpectra.calculateSpectra()
        self.pF.setSpectra(self.spotSpectra.getSpectra())
        self.pF.setWavelength(self.sCamera.wavelength)
        self.pF.calculateFit()
        # get the time sCamera
        newTime = self.sCamera.t0
        #newTime = time.time()
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

# TODO: test it!
if __name__ == '__main__':
    pass

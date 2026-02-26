"""
class emulating sCamera for reading spectral images from File

Created on Mon Nov 15 12:08:51 2021

@author: ostranik
"""
#%%

import os
import time
import numpy as np
from viscope.instrument.base.baseSequencer import BaseSequencer
from spectralCamera.algorithm.fileSIVideo import FileSIVideo


class SCameraFromFile(BaseSequencer):
    ''' class to emulating sCamera for delivering saved spectral images
    '''
    DEFAULT = {'name': 'SCameraFromFile'
                }

    def __init__(self, name=None, **kwargs):
        ''' initialisation '''

        if name== None: name= SCameraFromFile.DEFAULT['name']
        super().__init__(name=name, **kwargs)
        
        # spectralCamera parameters
        self.sImage = None
        self.wavelength = None
        self.t0 = time.time() # time of acquisition of the last spectral image
        
        # image file parameters
        self.fileSIVideo = FileSIVideo()
        self.fileName = None # list of files name
        self.fileTime = None # list of files time
        self.idx = [0] # indexes of files to process
    
        # processor, which has to be free in order to send next image
        self.processor = None

    def getWavelength(self):
        return self.wavelength        

    def getLastSpectralImage(self):
        ''' direct call of the camera image and spectral processing of it '''
        return self.sImage

    def setFolder(self,folder):
        ''' set folder with the images and get info about the files'''
        self.fileSIVideo.setFolder(folder)
        self.wavelength = self.fileSIVideo.loadWavelength()

        self.fileName, self.fileTime = self.fileSIVideo.getImageInfo()
        #nFiles = len(fileName)
        #self.fileTime = self.fileTime/1e9 # convert to seconds
        print(f'fileName {self.fileName}')

    def getFolder(self):
        ''' get current folder'''
        return self.fileSIVideo.folder

    def startReadingImages(self,idx=None):
        ''' initiate sending the spectral images'''
        if idx is None:
            self.idx = list(range(len(self.fileName)))
        else:
            self.idx = idx
        print('starting reading images')
        print(f' idx {self.idx}')
        self.worker.start()

    def connect(self,processor=None):
        ''' connect data processor with the camera '''
        if processor is not None:
            super().connect(processor.flagLoop)
            self.setParameter('processor',processor)
        else:
            super().connect()

    def setParameter(self,name, value):
        ''' set parameter of the spectral camera'''
        super().setParameter(name,value)

        if name== 'processor':
            self.processor = value
            self.flagToProcess = self.processor.flagLoop

    def getParameter(self,name):
        ''' get parameter of the camera '''
        _value = super().getParameter(name)
        if _value is not None: return _value        

        if name=='wavelength':
            return self.getWavelength()

        if name== 'processor':
            return self.processor

    def loop(self):
        ''' process new data file'''
        print('running processData loop in sCamera from File')
        
        for ii in self.idx:
            print(f'processing {ii} file')
            self.sImage = self.fileSIVideo.loadImage(self.fileName[ii])
            self.t0 = self.fileTime[ii]
            yield True
            self.flagLoop = True

            while not self.flagToProcess:
                time.sleep(0.003)



#%%

if __name__ == '__main__':
    pass




    def __init__(self, name=None, **kwargs):
        ''' initialisation '''

        if name== None: name= SCameraFromFile.DEFAULT['name']
        super().__init__(name=name, **kwargs)
        
        # spectral camera
        self.sCamera = None
        # spectral camera
        self.pump = None
        
        # data container
        self.pF = PlasmonFit()
        self.spotSpectra = SpotSpectra()
        self.spotData = SpotData()
        self.flowData = FlowData()


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
        print(f"processing data from {self.DEFAULT['name']}")
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
        if newFlow is not None:
            self.flowData.addDataValue([newFlow],newTime)
    

#%%

# TODO: test it!
if __name__ == '__main__':
    pass

"""
virtual basic microscope

components: camera

@author: ostranik
"""
#%%

import time

from viscope.virtualSystem.base.baseSystem import BaseSystem
from viscope.virtualSystem.component.component import Component
from plim.virtualSystem.component.sample3 import Sample3
from spectralCamera.virtualSystem.component.component2 import Component2
import numpy as np
import napari

class PlimMicroscope(BaseSystem):
    ''' class to emulate microscope '''
    DEFAULT = {'photonFlux':1e6}
               
    
    def __init__(self,*args, **kwargs):
        ''' initialisation '''
        super().__init__(*args, **kwargs)

        # set default spectral sample
        self.sample = Sample3()
        self.sample.setPlasmonArray(arraySize=np.array([7,7]))


    def setVirtualDevice(self,sCamera=None, camera2=None,stage=None):
        ''' set instruments of the microscope '''
        self.device['sCamera'] = sCamera
        self.device['camera'] = sCamera.camera
        self.device['camera2'] = camera2
        self.device['stage'] = stage


    def calculateVirtualFrameCamera(self):
        ''' update the virtual Frame of the spectral camera '''
        
        # image sample - absorbance
        iFrame=self.sample.get()
        # adjust wavelength
        iFrame = Component2.spectraRangeAdjustment(iFrame,self.sample.getWavelength(),self.device['sCamera'].getWavelength())
 
        # stage
        samplePosition = self.sample.position + self.device['stage'].position
        samplePositionXY = samplePosition[0:2]
        
        sCal = self.device['sCamera'].spectraCalibration
        oFrame = np.zeros((iFrame.shape[0],*sCal.nYX))
        Component.ideal4fImaging(iFrame=iFrame,oFrame=oFrame,iFramePosition = samplePositionXY,
                        magnification=0.5,iPixelSize=self.sample.pixelSize,oPixelSize=self.sample.pixelSize)


        #convert absorbance to photon flux
        oFrame = self.DEFAULT['photonFlux']/np.exp(oFrame)

        (oFrame, position00) = Component2.disperseIntoLines(oFrame, gridVector = sCal.gridVector)
    
        iFramePosition = sCal.position00 - position00 

        # image it onto camera-chip
        # convenient way to crop not full super-pixel
        oFrame = Component.ideal4fImagingOnCamera(camera=self.device['camera'],iFrame=oFrame,
                                iFramePosition=iFramePosition,iPixelSize=self.device['camera'].DEFAULT['cameraPixelSize'],
                                magnification=1)



        #print(f'oFrame.shape {oFrame.shape}')

        print('virtual Frame updated')

        return oFrame

    def calculateVirtualFrameCamera2(self):
        ''' update the virtual Frame of the black/white camera '''
        
        # image sample (absorption)
        iFrame=self.sample.get()

        # stage
        samplePosition = self.sample.position + self.device['stage'].position
        samplePositionXY = samplePosition[0:2]


        # 4f imaging onto chip of absorbance
        oFrame = np.zeros((iFrame.shape[0],self.device['camera2'].getParameter('height'),
                    self.device['camera2'].getParameter('width')))
        Component.ideal4fImaging(iFrame,oFrame,iFramePosition=samplePositionXY,magnification=4,iPixelSize=self.sample.pixelSize,
        oPixelSize= self.device['camera2'].DEFAULT['cameraPixelSize'])


        #convert absorbance to photon flux
        oFrame = self.DEFAULT['photonFlux']/np.exp(oFrame)

        # sum wavelength
        oFrame = np.sum(oFrame, axis= 0)

        #adjust the exposure

        ## integration time of the camera
        oFrame *= self.device['camera2'].exposureTime/1e6


        print('virtual Frame updated')

        return oFrame



    def loop(self):
        ''' infinite loop to carry out the microscope state update
        it is a state machine, which should be run in separate thread '''
        while True:
            yield 
            # recalculate cameras if stage moved
            if self.device['stage'].flagSetParameter.is_set():
                self.device['camera'].flagSetParameter.set()
                self.device['camera2'].flagSetParameter.set()
                self.device['stage'].flagSetParameter.clear()

            if self.device['camera'].flagSetParameter.is_set():
                print(f'calculate virtual frame - camera ')
                self.device['camera'].virtualFrame = self.calculateVirtualFrameCamera()
                self.device['camera'].flagSetParameter.clear()
            if self.device['camera2'].flagSetParameter.is_set():
                print(f'calculate virtual frame - camera2')
                self.device['camera2'].virtualFrame = self.calculateVirtualFrameCamera2()
                self.device['camera2'].flagSetParameter.clear()

            time.sleep(0.03)

        

#%%

if __name__ == '__main__':

    pass
# %%

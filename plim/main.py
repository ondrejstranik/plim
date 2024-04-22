'''
class for live viewing spectral images
'''
#%%

#import numpy as np
from viscope.main import Viscope
from viscope.gui.allDeviceGUI import AllDeviceGUI 
from plim.gui.stViewerGUI import STViewerGUI

from viscope.instrument.virtual.virtualCamera import VirtualCamera
from spectralCamera.instrument.sCamera.sCameraGenerator import VirtualIFCamera

from plim.virtualSystem.plimMicroscope import PlimMicroscope

class Plim():
    ''' base top class for control'''

    DEFAULT = {}

    @classmethod
    def run(cls):
        '''  set the all the parameter and then run the GUI'''

        #camera
        camera2 = VirtualCamera(name='BWCamera')
        camera2.connect()
        camera2.setParameter('threadingNow',True)

        #spectral camera system
        scs = VirtualIFCamera()

        camera = scs.camera
        sCamera = scs.sCamera

        # virtual microscope
        vM = PlimMicroscope()
        vM.setVirtualDevice(sCamera=sCamera, camera2=camera2)
        vM.sample.setCalibrationImage()
        vM.connect()

        # main event loop
        viscope = Viscope(name='plim')
        newGUI  = STViewerGUI(viscope)
        newGUI.setDevice(sCamera)

        viewer  = AllDeviceGUI(viscope)
        viewer.setDevice([camera,camera2])

        viscope.run()

        sCamera.disconnect()
        camera.disconnect()
        camera2.disconnect()
        vM.disconnect()


if __name__ == "__main__":

    Plim.run()



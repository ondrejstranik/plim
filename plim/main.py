'''
class for live viewing spectral images
'''
#%%

from viscope.main import Viscope
from viscope.gui.allDeviceGUI import AllDeviceGUI 
from plim.gui.plasmonViewerGUI import PlasmonViewerGUI
from plim.gui.positionTrackGUI import PositionTrackGUI


from viscope.instrument.virtual.virtualCamera import VirtualCamera
from spectralCamera.algorithm.calibrateIFImage import CalibrateIFImage
from spectralCamera.instrument.sCamera.sCamera import SCamera
from viscope.instrument.virtual.virtualStage import VirtualStage
from plim.instrument.plasmonProcessor import PlasmonProcessor


from plim.virtualSystem.plimMicroscope import PlimMicroscope

import numpy as np

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
        #camera
        VirtualCamera.DEFAULT['height']= 900
        camera = VirtualCamera(name='rawSpectralCamera')
        camera.connect()
        camera.setParameter('threadingNow',True)
        #spectral camera
        CalibrateIFImage.DEFAULT['position00']= np.array([550,0])
        sCal = CalibrateIFImage(camera=camera)
        sCamera = SCamera(name='spectralCamera')
        sCamera.connect()
        sCamera.setParameter('camera',camera)
        sCamera.setParameter('calibrationData',sCal)
        sCamera.setParameter('threadingNow',True)

        # stage
        stage = VirtualStage('stage')
        stage.connect()

        # plasmon data processo    
        pP = PlasmonProcessor()
        pP.connect(sCamera=sCamera)
        pP.setParameter('threadingNow',True)

        # virtual microscope
        vM = PlimMicroscope()
        vM.setVirtualDevice(sCamera=sCamera, camera2=camera2,stage=stage)
        vM.connect()

        # set GUIs
        viscope = Viscope(name='plim')
        viewer  = AllDeviceGUI(viscope)
        viewer.setDevice([stage,camera,camera2])

        _vWindow = viscope.addViewerWindow()
        newGUI  = PlasmonViewerGUI(viscope,vWindow=_vWindow)
        newGUI.setDevice(pP)

        newGUI  = PositionTrackGUI(viscope)
        newGUI.setDevice(pP)

        # main event loop
        viscope.run()

        sCamera.disconnect()
        camera.disconnect()
        camera2.disconnect()
        pP.disconnect()
        vM.disconnect()


if __name__ == "__main__":

    Plim.run()



'''
class for live viewing spectral images
'''
#%%

import plim
from viscope.main import viscope
from viscope.gui.allDeviceGUI import AllDeviceGUI 
from plim.gui.plasmonViewerGUI import PlasmonViewerGUI
from plim.gui.positionTrackGUI import PositionTrackGUI
from viscope.gui.cameraGUI import CameraGUI
from viscope.gui.cameraViewGUI import CameraViewGUI
from plim.gui.saveDataGUI import SaveDataGUI

from viscope.gui.saveImageGUI import SaveImageGUI

import numpy as np
from pathlib import Path

class Plim():
    ''' base top class for control'''

    DEFAULT = {}

    @classmethod
    def runVirtual(cls):
        '''  set the all the parameter and then run the GUI'''

        from viscope.instrument.virtual.virtualCamera import VirtualCamera
        from spectralCamera.algorithm.calibrateIFImage import CalibrateIFImage
        from spectralCamera.instrument.sCamera.sCamera import SCamera
        from viscope.instrument.virtual.virtualStage import VirtualStage
        from viscope.instrument.virtual.virtualPump import VirtualPump
        from plim.instrument.plasmonProcessor import PlasmonProcessor

        from plim.virtualSystem.plimMicroscope import PlimMicroscope


        # some global settings
        viscope.dataFolder = plim.dataFolder

        #camera
        camera2 = VirtualCamera(name='BWCamera')
        camera2.connect()
        camera2.setParameter('exposureTime', 300)
        camera2.setParameter('nFrame', 3)
        camera2.setParameter('threadingNow',True)

        #spectral camera system
        #camera
        VirtualCamera.DEFAULT['height']= 900
        camera = VirtualCamera(name='rawSpectralCamera')
        camera.connect()
        camera.setParameter('exposureTime', 300)
        camera.setParameter('nFrame', 3)
        camera.setParameter('threadingNow',True)
        #spectral camera
        CalibrateIFImage.DEFAULT['position00']= np.array([550,0])
        sCal = CalibrateIFImage(camera=camera)
        sCamera = SCamera(name='spectralCamera')
        sCamera.connect()
        sCamera.aberrationCorrection = True
        sCamera.setParameter('camera',camera)
        sCamera.setParameter('calibrationData',sCal)
        sCamera.setParameter('threadingNow',True)

        # stage
        stage = VirtualStage('stage')
        stage.connect()

        # pump
        pump = VirtualPump('pump')
        pump.connect()
        pump.setParameter('flowRate',30)
        pump.setParameter('flow',True)

        # plasmon data processor    
        pP = PlasmonProcessor()
        pP.connect(sCamera=sCamera, pump=pump)
        pP.setParameter('threadingNow',True)

        # virtual microscope
        vM = PlimMicroscope()
        vM.setVirtualDevice(sCamera=sCamera, camera2=camera2,stage=stage,pump=pump)
        vM.connect()

        # set GUIs
        viewer  = AllDeviceGUI(viscope)
        viewer.setDevice([stage,pump])
 
        deviceGUI = CameraGUI(viscope,vWindow=viscope.vWindow)
        deviceGUI.setDevice(camera)
        #deviceGUI = CameraViewGUI(viscope,vWindow='new')
        #deviceGUI.setDevice(camera)
        #deviceGUI = CameraGUI(viscope,vWindow=viscope.vWindow)
        #deviceGUI.setDevice(camera2)
        #deviceGUI = CameraViewGUI(viscope,vWindow='new')
        #deviceGUI.setDevice(camera2)
        newGUI  = PlasmonViewerGUI(viscope,vWindow='new')
        newGUI.setDevice(pP)
        newGUI2  = PositionTrackGUI(viscope,vWindow='new')
        newGUI2.setDevice(pP)
        deviceGUI = SaveDataGUI(viscope,vWindow=newGUI2.vWindow)
        deviceGUI.setDevice(pP)


        # carry out some GUI settings
        #newGUI.plasmonViewer.spotIdentGui()

        # main event loop
        viscope.run()

        sCamera.disconnect()
        camera.disconnect()
        camera2.disconnect()
        pP.disconnect()
        vM.disconnect()


    @classmethod
    def runReal(cls):
        '''  set the all the parameter and then run the GUI'''

        from spectralCamera.algorithm.calibrateFrom3Images import CalibrateFrom3Images
        from spectralCamera.instrument.sCamera.sCamera import SCamera
        from plim.instrument.pump.regloICC import RegloICC
        from plim.instrument.plasmonProcessor import PlasmonProcessor
        from spectralCamera.instrument.camera.milCamera.milCamera import MilCamera
        from viscope.instrument.virtual.virtualPump import VirtualPump  


        # some global settings
        viscope.dataFolder = plim.dataFolder

        #spectral camera system
        #camera
        camera = MilCamera(name='MilCamera')
        camera.connect()
        camera.setParameter('exposureTime', 5)
        camera.setParameter('nFrame', 24)
        camera.setParameter('threadingNow',True)
        #spectral camera

        sCal = CalibrateFrom3Images()
        sCal = sCal.loadClass(classFile = r'C:\Users\ostranik\Documents\GitHub\spectralCamera\spectralCamera\DATA\24-06-26-calibration\CalibrateFrom3Images.obj')
        sCamera = SCamera(name='spectralCamera')
        sCamera.connect()
        sCamera.aberrationCorrection = True
        sCamera.setParameter('camera',camera)
        sCamera.setParameter('calibrationData',sCal)
        sCamera.setParameter('threadingNow',True)

        # pump
        #pump = VirtualPump('pump')
        RegloICC.DEFAULT['port'] = 'COM3'
        pump = RegloICC('pump')
        pump.connect()
        pump.setParameter('flowRate',30)
        pump.setParameter('flow',False)

        # plasmon data processor    
        pP = PlasmonProcessor()
        pP.connect(sCamera=sCamera, pump=pump)
        pP.setParameter('threadingNow',True)

        # set GUIs
        viewer  = AllDeviceGUI(viscope)
        viewer.setDevice([pump,camera])

        #deviceGUI = CameraGUI(viscope,vWindow=viscope.vWindow)
        #deviceGUI.setDevice(camera)
        #deviceGUI = CameraViewGUI(viscope,vWindow='new')
        #deviceGUI.setDevice(camera)
        #deviceGUI = CameraGUI(viscope,vWindow=viscope.vWindow)
        #deviceGUI.setDevice(camera2)
        #deviceGUI = CameraViewGUI(viscope,vWindow='new')
        #deviceGUI.setDevice(camera2)
        newGUI  = PlasmonViewerGUI(viscope,vWindow='new')
        newGUI.setDevice(pP)
        newGUI2  = PositionTrackGUI(viscope,vWindow='new')
        newGUI2.setDevice(pP)
        deviceGUI = SaveDataGUI(viscope,vWindow=newGUI2.vWindow)
        deviceGUI.setDevice(pP)


        # carry out some GUI settings
        #newGUI.plasmonViewer.spotIdentGui()

        # main event loop
        viscope.run()

        sCamera.disconnect()
        camera.disconnect()
        pP.disconnect()

if __name__ == "__main__":

    #Plim.runReal()
    Plim.runVirtual()
    
#%%


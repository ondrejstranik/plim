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
from spectralCamera.gui.sCameraGUI import SCameraGUI
from plim.gui.saveDataGUI import SaveDataGUI
from spectralCamera.gui.saveSIVideoGUI import SaveSIVideoGUI

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
        adGui  = AllDeviceGUI(viscope)
        adGui.setDevice([stage,pump])
 
        cGui = CameraGUI(viscope)
        cGui.setDevice(camera)
        scGui = SCameraGUI(viscope)
        scGui.setDevice(sCamera)
        cvGui = CameraViewGUI(viscope,vWindow='new')
        cvGui.setDevice(camera)
        #deviceGUI = CameraGUI(viscope,vWindow=viscope.vWindow)
        #deviceGUI.setDevice(camera2)
        #deviceGUI = CameraViewGUI(viscope,vWindow='new')
        #deviceGUI.setDevice(camera2)
        pvGui  = PlasmonViewerGUI(viscope,vWindow='new')
        pvGui.setDevice(pP)
        ptGui  = PositionTrackGUI(viscope,vWindow='new')
        ptGui.setDevice(pP)
        ptGui.interconnectGui(pvGui)
        sdGui = SaveDataGUI(viscope,vWindow=ptGui.vWindow)
        sdGui.setDevice(pP)
        svGui  = SaveSIVideoGUI(viscope)
        svGui.setDevice(sCamera)

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
        # this is necessary, because the saved sCal does not have gridLine.spBlockRowIdx and gridLine.spBlockColumnIdx 
        sCal.gridLine.spBlockRowIdx = None
        sCal.gridLine.spBlockColumnIdx = None

        sCamera = SCamera(name='spectralCamera')
        sCamera.connect()
        sCamera.aberrationCorrection = True
        sCamera.setParameter('camera',camera)
        sCamera.setParameter('calibrationData',sCal)
        sCamera.setParameter('threadingNow',True)

        # pump
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
        adGui  = AllDeviceGUI(viscope)
        adGui.setDevice(pump)
        
        cGui = CameraGUI(viscope)
        cGui.setDevice(camera)
        scGui = SCameraGUI(viscope)
        scGui.setDevice(sCamera)
        cvGui = CameraViewGUI(viscope,vWindow='new')
        cvGui.setDevice(camera)

        pvGui  = PlasmonViewerGUI(viscope,vWindow='new')
        pvGui.setDevice(pP)
        ptGui  = PositionTrackGUI(viscope,vWindow='new')
        ptGui.setDevice(pP)
        ptGui.interconnectGui(pvGui)
        sdGui = SaveDataGUI(viscope,vWindow=ptGui.vWindow)
        sdGui.setDevice(pP)
        svGui  = SaveSIVideoGUI(viscope)
        svGui.setDevice(sCamera)


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


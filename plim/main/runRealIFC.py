'''
script to run plasmon sensing with real instruments
camera based on integral field technology
'''
#%%

# devices
from spectralCamera.algorithm.calibrateFrom3Images import CalibrateFrom3Images
from spectralCamera.instrument.sCamera.sCamera import SCamera
from plim.instrument.pump.regloICC import RegloICC
from plim.instrument.plasmonProcessor import PlasmonProcessor
from spectralCamera.instrument.camera.milCamera.milCamera import MilCamera

# gui
import plim
from viscope.main import viscope
from viscope.gui.allDeviceGUI import AllDeviceGUI 
from plim.gui.plasmonViewerGUI import PlasmonViewerGUI
from plim.gui.positionTrackGUI import PositionTrackGUI
from viscope.gui.cameraGUI import CameraGUI
from viscope.gui.cameraViewGUI import CameraViewGUI
from viscope.gui.cameraView2GUI import CameraView2GUI
from spectralCamera.gui.sCameraGUI import SCameraGUI
from plim.gui.saveDataGUI import SaveDataGUI
from spectralCamera.gui.saveSIVideoGUI import SaveSIVideoGUI
from viscope.gui.saveImageGUI import SaveImageGUI
from viscope.gui.histogramGUI import HistogramGUI


def main():
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
    sCal = sCal.loadClass(classFile = r'C:\Users\ostranik\Documents\GitHub\spectralCamera\spectralCamera\DATA\26-02-11-calibration\CalibrateFrom3Images.obj')
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
    RegloICC.DEFAULT['port'] = 'COM4'
    RegloICC.DEFAULT['serialNo'] = 'H21002980'
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
    cvGui = CameraView2GUI(viscope,vWindow='new')
    cvGui.setDevice(camera)
    
    #cvGui = CameraViewGUI(viscope,vWindow='new')
    #cvGui.setDevice(camera)

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
    main()
    
#%%


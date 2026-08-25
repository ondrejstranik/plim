'''
script to run plasmon sensing with real instruments
camera based on multi filter camera technology
'''
#%%

# gui must be imported before camera SDK to ensure PyQt5 DLLs are loaded first
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
from plim.gui.signalAnalyser.fitGUI import FitGUI

# devices (imported after GUI to avoid DLL conflicts with camera SDK on Windows)
from spectralCamera.instrument.camera.pfCamera.pFCamera import PFCamera
from spectralCamera.algorithm.calibratePFImage import CalibratePFImage
from spectralCamera.instrument.sCamera.sCamera import SCamera
from plim.instrument.pump.regloICC import RegloICC
from plim.instrument.plasmonProcessor import PlasmonProcessor


def main():
    # some global settings
    viscope.dataFolder = plim.dataFolder

    #spectral camera system
    #camera
    camera = PFCamera(name='pfCamera')
    camera.connect()
    camera.setParameter('exposureTime',10)
    camera.setParameter('nFrame',5)

    camera.setParameter('threadingNow',True)

    sCal = CalibratePFImage()
    
    sCamera = SCamera(name='spectralCamera')
    sCamera.connect()
    sCamera.aberrationCorrection = True
    sCamera.setParameter('camera',camera)
    sCamera.setParameter('calibrationData',sCal)
    sCamera.setParameter('threadingNow',True)

    # pump
    #pump = VirtualPump('pump')
    RegloICC.DEFAULT['port'] = 'COM7'
    pump = RegloICC('pump')
    
    pump.connect()
    pump.setParameter('flowRate',30)
    pump.setParameter('flow',False)


    # plasmon data processor
    pP = PlasmonProcessor()
    pP.connect(sCamera=sCamera, pump=pump)
    pP.setParameter('loopDelay',1) # throttle down the fitting loop to reduce GUI freezing
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
    #hiGUI  = HistogramGUI(viscope,vWindow = cvGui.vWindow)
    #hiGUI.setDevice(camera)

    pvGui  = PlasmonViewerGUI(viscope,vWindow='new')
    pvGui.setDevice(pP)
    pvGui.plasmonViewer.fitParameterGui(peakWidth=80,wavelengthStart=700, wavelengthStop=900)
    pvGui.plasmonViewer.spectraParameterGui(showRawSpectra=False,
                                            circle=False,
                                             spectraSigma=1,
                                             pxBcg= 4,

                                               pxSpace=2)

    ptGui  = PositionTrackGUI(viscope,vWindow='new')
    ptGui.setDevice(pP)
    ptGui.interconnectGui(pvGui)
    ptGui.positionTrack.fitParameter(align=True)
    sdGui = SaveDataGUI(viscope,vWindow=cGui.vWindow)
    sdGui.setDevice(pP)
    svGui  = SaveSIVideoGUI(viscope)
    svGui.setDevice(sCamera)

    fitGui = FitGUI(viscope, vWindow=ptGui.vWindow)
    fitGui.interconnectGui(ptGui)

    # place the windows
    adGui.vWindow.setRegion('right')
    ptGui.vWindow.setRegion('right')
    viscope.wManager.setRegionRatio('right', 0.45) 
    viscope.wManager.setVWindowAlignment('overlap')

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


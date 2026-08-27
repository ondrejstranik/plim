''' standalone script version of plim.main.runVirtualIFC for running the
virtual integral-field-camera plasmon sensing demo on https://mybinder.org/ '''

from viscope.logger.verbosity import setVerbosity

# devices
from viscope.instrument.virtual.virtualCamera import VirtualCamera
from spectralCamera.algorithm.calibrateIFImage import CalibrateIFImage
from spectralCamera.instrument.sCamera.sCamera import SCamera
from viscope.instrument.virtual.virtualStage import VirtualStage
from viscope.instrument.virtual.virtualPump import VirtualPump
from plim.instrument.plasmonProcessor import PlasmonProcessor
from plim.virtualSystem.plimMicroscope import PlimMicroscope

# gui
import plim
from viscope.main import viscope
from viscope.gui.allDeviceGUI import AllDeviceGUI
from plim.gui.plasmonViewerGUI import PlasmonViewerGUI
from plim.gui.positionTrackGUI import PositionTrackGUI
from viscope.gui.cameraGUI import CameraGUI
from viscope.gui.cameraView2GUI import CameraView2GUI
from spectralCamera.gui.sCameraGUI import SCameraGUI
from plim.gui.saveDataGUI import SaveDataGUI
from spectralCamera.gui.saveSIVideoGUI import SaveSIVideoGUI
from plim.gui.signalAnalyser.fitGUI import FitGUI
from plim.gui.deltaSignalGUI import DeltaSignalGUI

import numpy as np


# some global settings

# log only info and errors (suppress the debug-level per-frame chatter)
setVerbosity('INFO')
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
pump.setParameter('flowRate',-30)
pump.setParameter('flow',True)

# plasmon data processor
pP = PlasmonProcessor()
pP.connect(sCamera=sCamera, pump=pump)
#pP.setParameter('loopDelay',1) # throttle down the fitting loop to reduce GUI freezing
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
cvGui = CameraView2GUI(viscope,vWindow='new')
cvGui.setDevice(camera)
pvGui  = PlasmonViewerGUI(viscope,vWindow='new')
pvGui.setDevice(pP)
pvGui.plasmonViewer.fitParameterGui(peakWidth=80)
pvGui.plasmonViewer.spectraParameterGui(showRawSpectra=False, pxSpace=2)
ptGui  = PositionTrackGUI(viscope,vWindow='new')
ptGui.setDevice(pP)
ptGui.interconnectGui(pvGui)
ptGui.positionTrack.fitParameter(align=True)
sdGui = SaveDataGUI(viscope,vWindow=adGui.vWindow)
sdGui.setDevice(pP)
svGui  = SaveSIVideoGUI(viscope,vWindow=adGui.vWindow)
svGui.setDevice(sCamera)
dsGui  = DeltaSignalGUI(viscope,vWindow=ptGui.vWindow)
dsGui.setDevice(pP)
dsGui.interconnectGui(pvGui,ptGui)


fitGui = FitGUI(viscope, vWindow=ptGui.vWindow)
fitGui.interconnectGui(ptGui)


# place the windows
adGui.vWindow.setRegion('right')
ptGui.vWindow.setRegion('right')
viscope.wManager.setRegionRatio('right', 0.45)
viscope.wManager.setVWindowAlignment('overlap')
# mybinder.org's remote desktop doesn't keep its taskbar's reserved space
# in sync with QScreen.availableGeometry(), so windows can end up placed
# behind it - reserve that space manually instead
viscope.wManager.setScreenMargin(bottom=40)


# main event loop
viscope.run()

pvGui.viewer.close()
cvGui.viewer.close()

pump.disconnect()
sCamera.disconnect()
camera.disconnect()
camera2.disconnect()
pP.disconnect()
vM.disconnect()

'''
script for viewing recorded spectral images and generating signals
'''
#%%

from spectralCamera.instrument.sCamera.sCameraFromFile import SCameraFromFile
from plim.instrument.plasmonProcessor import PlasmonProcessor

from viscope.main import viscope
from plim.gui.plasmonViewerGUI import PlasmonViewerGUI
from spectralCamera.gui.sCameraFromFileGUI import SCameraFromFileGUI
from plim.gui.saveDataGUI import SaveDataGUI
from plim.gui.positionTrackGUI import PositionTrackGUI


#spectral camera system
fFolder = r'G:\office\work\git\plim\plim\DATA\test_video'
sCamera = SCameraFromFile()
sCamera.connect()
sCamera.setParameter('threadingNow',True)  
sCamera.setFolder(fFolder)

# plasmon processor 
pP = PlasmonProcessor()
pP.connect(sCamera=sCamera)
pP.setParameter('threadingNow',True)
sCamera.setParameter('processor',pP)

# add gui
pvGui  = PlasmonViewerGUI(viscope)
pvGui.setDevice(pP)

scGUI  = SCameraFromFileGUI(viscope)
scGUI.setDevice(sCamera)

ptGui  = PositionTrackGUI(viscope,vWindow='new')
ptGui.setDevice(pP)
ptGui.interconnectGui(pvGui)
sdGui = SaveDataGUI(viscope,vWindow=ptGui.vWindow)
sdGui.setDevice(pP)

# main event loop
viscope.run()

sCamera.disconnect()
pP.disconnect()

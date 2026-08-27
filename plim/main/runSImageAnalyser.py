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
from plim.gui.deltaSignalGUI import DeltaSignalGUI


def main():

    #spectral camera system
    fFolder = r'G:\office\work\git\plim\plim\DATA\test_video'
    fFolder = r'F:\ondra\LPI\plim\DATA\tunableFilterBased\26-07-30 Tomas_sensitivity\LbL\04_Bulk_sensitivity_pumpplan_0-70percent_to_LbL_with_water_v1_LED_V2\images'
    sCamera = SCameraFromFile()
    sCamera.connect()
    sCamera.setParameter('threadingNow',True)

    # plasmon processor
    pP = PlasmonProcessor()
    pP.connect(sCamera=sCamera)
    pP.setParameter('loopDelay',0.1) # throttle down the fitting loop to reduce GUI freezing
    pP.setParameter('threadingNow',True)
    sCamera.setParameter('processor',pP)

    # add gui
    scGui  = SCameraFromFileGUI(viscope)
    scGui.setDevice(sCamera)

    pvGui  = PlasmonViewerGUI(viscope,vWindow='new')
    pvGui.setDevice(pP)

    ptGui  = PositionTrackGUI(viscope,vWindow='new')
    ptGui.setDevice(pP)
    ptGui.interconnectGui(pvGui)

    sdGui = SaveDataGUI(viscope,vWindow=scGui.vWindow)
    sdGui.setDevice(pP)

    dsGui  = DeltaSignalGUI(viscope,vWindow=ptGui.vWindow)
    dsGui.setDevice(pP)
    dsGui.interconnectGui(pvGui,ptGui)


    # now that every GUI is wired up (pvGui/ptGui listening to pP), select
    # the folder and load the first image - explicit and independent of
    # construction order, unlike setting it as a side effect of setDevice()
    scGui.selectFileGui(filePath=fFolder)

    # place the windows
    scGui.vWindow.setRegion('right')
    ptGui.vWindow.setRegion('right')
    viscope.wManager.setRegionRatio('right', 0.45) 

    # main event loop
    viscope.run()

    sCamera.disconnect()
    pP.disconnect()


if __name__ == "__main__":
    main()
    
#%%
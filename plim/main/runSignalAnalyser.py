'''
script to run analysis of plasmon signals
'''
#%%
from viscope.main import viscope

from plim.instrument.fileDataProcessor import FileDataProcessor
from plim.gui.positionTrackGUI import PositionTrackGUI
from plim.gui.signalAnalyser.spotViewerGUI import SpotViewerGUI
from plim.gui.signalAnalyser.fitGUI import FitGUI
from plim.gui.signalAnalyser.fileDataProcessorGUI import FileDataProcessorGUI


def main():

    device = FileDataProcessor()
    device.connect()

    fileDataGui = FileDataProcessorGUI(viscope)

    spotViewerGui = SpotViewerGUI(viscope, vWindow='new')
    ptGui = PositionTrackGUI(viscope, vWindow='new')
    fitGui = FitGUI(viscope, vWindow=ptGui.vWindow)

    ptGui.setDevice(device)
    spotViewerGui.setDevice(device)
    fitGui.setDevice(device)
    fileDataGui.setDevice(device)

    ptGui.interconnectGui(spotViewerGui)
    fitGui.interconnectGui(ptGui)
    fileDataGui.interconnectGui(ptGui, spotViewerGui)

    # place the windows
    fileDataGui.vWindow.setRegion('top')
    viscope.wManager.setRegionRatio('top', 0.20) 

    # simulate pressing 'Load' once at startup
    #fileDataGui.selectAndLoad()

    # main event loop
    viscope.run()

    device.disconnect()


if __name__ == "__main__":
    main()

#%%

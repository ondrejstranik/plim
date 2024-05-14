'''
class for live viewing spectral images
'''
#%%
from spectralCamera.gui.xywViewerGUI import XYWViewerGui
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from qtpy.QtCore import Signal


class PlasmonViewerGUI_2(XYWViewerGui):
    ''' main class to show  plasmonViewer'''

    DEFAULT = {'nameGUI': 'PlasmonViewer'}
    sigPlasmonPeak = Signal(list)

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # prepare the gui of the class
        PlasmonViewerGUI_2.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        self.plasmonViewer = PlasmonViewer(show=False)
        self.viewer = self.plasmonViewer.viewer

        self.vWindow.addMainGUI(self.viewer.window._qt_window, name=self.DEFAULT['nameGUI'])

    def setDevice(self,device):
        super().setDevice(device)
        self.plasmonViewer.pF = self.device.pF
        self.plasmonViewer.spotSpectra = self.device.spotSpectra
        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)
        self.vWindow.setWindowTitle(self.device.name)

    def updateGui(self):
        ''' update the data in gui '''
        # napari
        #self.plasmonViewer.setWavelength(self.device.wavelength)
        self.plasmonViewer.xywImage = self.device.spotSpectra.wxyImage
        self.plasmonViewer.wavelength = self.device.pF.wavelength
        self.plasmonViewer.redraw()
        #self.sigPlasmonPeak.emit(self.plasmonViewer.pF.getPosition())



if __name__ == "__main__":
    pass

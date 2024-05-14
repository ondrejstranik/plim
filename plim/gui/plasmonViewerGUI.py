'''
class for live viewing spectral images
'''
#%%
from spectralCamera.gui.xywViewerGUI import XYWViewerGui
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from qtpy.QtCore import Signal


class PlasmonViewerGUI(XYWViewerGui):
    ''' main class to show  plasmonViewer'''

    DEFAULT = {'nameGUI': 'PlasmonViewer'}
    sigPlasmonPeak = Signal(list)

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # prepare the gui of the class
        PlasmonViewerGUI.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        self.plasmonViewer = PlasmonViewer(show=False)
        self.viewer = self.plasmonViewer.viewer

        self.vWindow.addMainGUI(self.viewer.window._qt_window, name=self.DEFAULT['nameGUI'])

    def setDevice(self,device):
        super().setDevice(device)
        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)
        self.vWindow.setWindowTitle(self.device.name)


    def updateGui(self):
        ''' update the data in gui '''
        # napari
        self.plasmonViewer.setWavelength(self.device.wavelength)
        self.plasmonViewer.setImage(self.device.sImage)
        self.sigPlasmonPeak.emit(self.plasmonViewer.pF.getPosition())



if __name__ == "__main__":
    pass

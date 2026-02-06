'''
class for live viewing spectral images
'''
#%%
#from spectralCamera.gui.xywViewerGUI import XYWViewerGui
from viscope.gui.baseGUI import BaseGUI
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer
from qtpy.QtCore import Signal


class PlasmonViewerGUI(BaseGUI):
    ''' main class to show  plasmonViewer
    this Viewer is connected to a processor, which calculates the spectra and fits in his thread
    '''

    DEFAULT = {'nameGUI': 'PlasmonViewer'}

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
        ''' the device is a processor, which calculate the spectra and fits'''
        super().setDevice(device)
        # connect data containers
        self.plasmonViewer.pF = self.device.pF
        self.plasmonViewer.spotSpectra = self.device.spotSpectra
        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)

    def updateGui(self):
        ''' update the data in gui '''
        # napari
        #self.plasmonViewer.setWavelength(self.device.pF.wavelength)
        #self.plasmonViewer.setImage(self.device.spotSpectra.image)
        #self.plasmonViewer.setWavelength(self.device.pF.wavelength)
        #self.plasmonViewer.calculateSpectra()
        self.plasmonViewer.redraw(modified='image')




if __name__ == "__main__":
    pass

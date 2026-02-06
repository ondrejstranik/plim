'''
class for live viewing spectral images
'''
#%%
from viscope.gui.baseGUI import BaseGUI
from plim.gui.spectralViewer.spotSpectraViewer import SpotSpectraViewer

class STViewerGUI(BaseGUI):
    ''' main class to show  spot transmission Viewer (called spotSpectraViewer)
    calculation of the spectra are done in the main thread of the SViewer
    '''

    DEFAULT = {'nameGUI': 'stViewer'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # prepare the gui of the class
        STViewerGUI.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        self.STViewer = SpotSpectraViewer(show=False)
        self.viewer = self.STViewer.viewer

        self.vWindow.addMainGUI(self.viewer.window._qt_window, name=self.DEFAULT['nameGUI'])

    def setDevice(self,device):
        super().setDevice(device)
        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)

    def updateGui(self):
        ''' update the data in gui '''
        # napari
        self.STViewer.setWavelength(self.device.wavelength)
        self.STViewer.setImage(self.device.sImage)



if __name__ == "__main__":
    pass

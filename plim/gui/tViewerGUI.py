'''
class for live viewing spectral images
'''
#%%
from spectralCamera.gui.xywViewerGUI import XYWViewerGui
from plim.gui.spectralViewer.transmissionViewer import TransmissionViewer

class TViewerGui(XYWViewerGui):
    ''' main class to show transmissionViewer'''

    DEFAULT = {'nameGUI': 'tViewer'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # prepare the gui of the class
        TViewerGui.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        self.TransmissionViewer = TransmissionViewer(show=False)
        self.viewer = self.TransmissionViewer.viewer

        self.vWindow.addMainGUI(self.viewer.window._qt_window, name=self.DEFAULT['nameGUI'])

    def updateGui(self):
        ''' update the data in gui '''
        # napari
        self.TransmissionViewer.setImage(self.device.sImage)
        self.TransmissionViewer.setWavelength(self.device.wavelength)


if __name__ == "__main__":
    pass


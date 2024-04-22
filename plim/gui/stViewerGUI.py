'''
class for live viewing spectral images
'''
#%%
from spectralCamera.gui.xywViewerGUI import XYWViewerGui
from plim.gui.spectralViewer.spotSpectraViewer import SpotSpectraViewer

class STViewerGUI(XYWViewerGui):
    ''' main class to show  spot transmission Viewer (called spotSpectraViewer)'''

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

    def updateGui(self):
        ''' update the data in gui '''
        # napari
        self.STViewer.setImage(self.device.sImage)
        self.STViewer.setWavelength(self.device.wavelength)


if __name__ == "__main__":
    pass

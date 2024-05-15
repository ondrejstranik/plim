'''
class for tracking of plasmon peaks
'''
#%%
#import napari
#from magicgui import magicgui
#from typing import Annotated, Literal

#from qtpy.QtWidgets import QLabel, QSizePolicy
#from qtpy.QtCore import Qt
from viscope.gui.baseGUI import BaseGUI
from plim.gui.signalViewer.signalWidget  import SignalWidget



import numpy as np

# TODO: plot the graph 
# record the peak position at every time camera takes an image and not at GUI update time !!!
class PositionTrackGUI(BaseGUI):
    ''' main class to show time evolution of plasmon peak position'''

    DEFAULT = {'nameGUI': 'Plasmon Signal'}


    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # widget
        self.positionTrack = None

        # prepare the gui of the class
        PositionTrackGUI.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        # add widget positionTrackGui
        self.positionTrack = SignalWidget()
        self.dw = self.vWindow.addMainGUI(self.positionTrack,name=self.DEFAULT['nameGUI'])

    def setDevice(self,device):
        super().setDevice(device)
        # connect data container
        self.positionTrack.sD = self.device.spotData
        
        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)

    def updateGui(self):
        ''' update the data in gui '''
        self.positionTrack.drawGraph()
  

if __name__ == "__main__":
        from viscope.instrument.virtual.virtualCamera import VirtualCamera
        from viscope.main import Viscope

        camera = VirtualCamera(name='camera1')
        camera.connect()
        camera.setParameter('threadingNow',True)

        viscope = Viscope()
        newGUI  = CameraViewGUI(viscope)
        newGUI.setDevice(camera)
        viscope.run()

        camera.disconnect()



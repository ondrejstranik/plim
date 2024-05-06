'''
class for tracking of plasmon peaks
'''
#%%
#import napari
from magicgui import magicgui
#from typing import Annotated, Literal

#from qtpy.QtWidgets import QLabel, QSizePolicy
#from qtpy.QtCore import Qt
from viscope.gui.baseGUI import BaseGUI

from timeit import default_timer as timer

import numpy as np

# TODO: plot the graph 
# record the peak position at every time camera takes an image and not at GUI update time !!!
class PositionTrackGUI(BaseGUI):
    ''' main class to show time evolution of plasmon peak position'''

    DEFAULT = {'nameGUI': 'Plasmon Signal'}


    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        
        self.lastUpdateTime = timer()
        self.guiUpdateTime = 0.03

        # widget
        self.positionTrackGui = None

        # prepare the gui of the class
        PositionTrackGUI.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        # add widget positionTrackGui
        self.positionTrackGui = pg.plot()
        self.positionTrackGui.setTitle(f'Peak Position')
        styles = {'color':'r', 'font-size':'20px'}
        self.positionTrackGui.setLabel('left', 'Position', units='nm')
        self.positionTrackGui.setLabel('bottom', 'time', units= 's')
        self.dw = self.vWindow.addParameterGui(self.positionTrackGui,name=self.DEFAULT['nameGUI'])
        

    def guiUpdateTimed(self):
        ''' update gui according the update time '''
        timeNow = timer()
        if (timeNow -self.lastUpdateTime) > self.guiUpdateTime:
            self.updateGui()
            self.lastUpdateTime = timeNow    

    def setDataSource(self,source):
        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)
        self.vWindow.setWindowTitle(self.device.name)


    def updateGui(self):
        ''' update the data in gui '''
        # napari
        self.rawLayer.data = self.device.rawImage


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



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
        
    def setDataSignal(self,signal):
        ''' set a signal, which connect new Data arrival with graph update '''  
        signal.connect(self.updateGraph)

    #TODO: finish this function !!!
    def updateGraph(self,newData):
        ''' update Graph with plasmon position '''
        try:
            self.positionTrackGui.clear()
            self.lineplotList5 = []

            npPosition = np.array(self.positionList)

            for ii in np.arange(npPosition.shape[1]):
                mypen = QPen(QColor.fromRgbF(*list(
                    self.pointLayer.face_color[ii])))
                mypen.setWidth(0)
                lineplot = self.positionTrackGui.plot(pen= mypen)
                lineplot.setData(self.timeList,
                    npPosition[:,ii],
                    symbol ='o',
                    symbolSize = 14,
                    symbolBrush = QColor.fromRgbF(*list(self.pointLayer.face_color[ii])),
                    pen= mypen)
                self.lineplotList5.append(lineplot)
        except:
             print('error occurred in drawPeakPositionGraph') 






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



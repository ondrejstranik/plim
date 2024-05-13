'''
class for viewing signals from spots' plasmon resonance
'''

import napari
import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QLabel, QSizePolicy,QWidget, QApplication, QVBoxLayout
from qtpy.QtCore import Qt
from magicgui import magicgui

import numpy as np
from plim.algorithm.spotData import SpotData


class SignalWidget(QWidget):
    ''' main class for viewing signal'''

    def __init__(self,signal=None, time= None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        self.sD = SpotData(signal,time)

        self.align = False
        self.alignTime = 0

        # set this gui of this class
        SignalWidget._setWidget(self)

        self.drawGraph()

    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(auto_call=True)
        def fitParameter(
            align: bool = self.align,
            alignTime: float = self.alignTime
            ):
            self.align= align
            self.alignTime = alignTime

            self.drawGraph()


        # add graph
        self.graph = pg.plot()
        self.graph.setTitle(f'Peak Position')
        styles = {'color':'r', 'font-size':'20px'}
        self.graph.setLabel('left', 'Position', units='nm')
        self.graph.setLabel('bottom', 'time', units= 's')
        self.graph.scene().sigMouseClicked.connect(self.mouse_clicked)

        # fit parameter
        self.fitParameter = fitParameter

        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        layout.addWidget(self.fitParameter.native)
        self.setLayout(layout)

    def mouse_clicked(self,evt):
        vb = self.graph.plotItem.vb
        scene_coords = evt.scenePos()
        if self.graph.sceneBoundingRect().contains(scene_coords):
            mouse_point = vb.mapSceneToView(scene_coords)
            self.fitParameter.alignTime.value = mouse_point.x()

    def drawGraph(self):
        ''' draw all new lines in the spectraGraph '''
        # remove all lines
        self.graph.clear()

        (signal, time) = self.sD.getData()

        if self.align:
            offSet = signal[np.argmin(np.abs(time - self.alignTime)),:]
        else:
            offSet = np.zeros(signal.shape[1])

        #try:
            # draw lines
        for ii in np.arange(signal.shape[1]):
            mypen = QPen()
            mypen.setWidth(0)
            #lineplot = self.graph.plot(pen= mypen)
            lineplot = self.graph.plot()

            lineplot.setData(time, signal[:,ii]-offSet[ii])
        #except:
        #    print('error occurred in drawSpectraGraph - pointSpectra')

    def setData(self, signal,time=None):
        ''' set the data '''
        self.sD.setData(signal,time)
        self.drawGraph()

    def addDataValue(valueVector,time):
        ''' add new value '''        
        self.sD.addDataValue(valueVector,time)
        self.drawGraph()


if __name__ == "__main__":
    from plim.gui.signalViewer.signalWidget import SignalWidget
    import numpy as np

    app = QApplication([])

    sV = SignalWidget(np.random.rand(50,4))
    sV.show()
    app.exec()

        















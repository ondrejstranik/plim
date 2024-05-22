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
from plim.algorithm.flowData import FlowData


class FlowRateWidget(QWidget):
    ''' main class for viewing flow rates of the pump channel'''
    DEFAULT = {'nameGUI':'FlowRate'
    }

    def __init__(self,signal=None, time= None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        self.flowData = FlowData(signal,time)

        # set this gui of this class
        FlowRateWidget._setWidget(self)

        self.drawGraph()

    def _setWidget(self):
        ''' prepare the gui '''

        # add graph
        self.graph = pg.plot()
        self.graph.setTitle(f'Flow Rate')
        styles = {'color':'r', 'font-size':'20px'}
        self.graph.setLabel('left', 'Flow Rate', units='ul/min')
        self.graph.setLabel('bottom', 'time', units= 's')

        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        self.setLayout(layout)

    def drawGraph(self):
        ''' draw all new lines in the spectraGraph '''

        (signal, time) = self.flowData.getData()

        # if there is no signal then do not continue
        if signal is None:
            return

        # remove all lines
        self.graph.clear()

        # draw lines
        for ii in np.arange(signal.shape[1]):
            mypen = QPen()
            mypen.setWidth(0)
            lineplot = self.graph.plot()

            lineplot.setData(time, signal[:,ii])

    def setData(self, signal,time=None):
        ''' set the data '''
        self.flowData.setData(signal,time)
        self.drawGraph()

    def addDataValue(valueVector,time):
        ''' add new value '''        
        self.flowData.addDataValue(valueVector,time)
        self.drawGraph()


if __name__ == "__main__":
    from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
    import numpy as np

    app = QApplication([])

    sV = FlowRateWidget(np.random.rand(50,4))
    sV.show()
    app.exec()

        















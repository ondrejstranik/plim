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
    DEFAULT = {'nameGUI':'FlowRate',
               'maxNLine': 4, # maxNLine ... max number of line plotted in the gra
            }

    def __init__(self,signal=None, time= None, flowData=None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        if flowData is not None: self.flowData= flowData 
        else:
            self.flowData = FlowData(signal,time)

        self.linePlotList = []
        self.maxNLine = FlowRateWidget.DEFAULT['maxNLine']

        # set this gui of this class
        FlowRateWidget._setWidget(self)

        self.drawGraph()

    def _setWidget(self):
        ''' prepare the gui '''
        
        # add graph Widget
        self.graph = pg.PlotWidget()
        self.graph.setTitle(f'Flow Rate')
        styles = {'color':'r', 'font-size':'20px'}
        self.graph.setLabel('left', 'Flow Rate', units='ul/min')
        self.graph.setLabel('bottom', 'time', units= 's')
        # pre allocate lines for the graph
        for ii in range(self.maxNLine):
            self.linePlotList.append(self.graph.plot())
            self.linePlotList[-1].hide()
  
        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        self.setLayout(layout)

    def drawGraph(self):
        ''' draw all valid lines in the graph '''
        # copy the data
        (signal, time) = self.flowData.getData()
        # if there is no signal then do not continue
        if signal is None:
            return
        nSig = signal.shape[1]

        # define pen object
        mypen = QPen()
        mypen.setColor(QColor("White"))
        mypen.setWidth(0)
        mypen.setStyle(1)

        self.graph.setUpdatesEnabled(False)
        # update data         
        for ii in np.arange(nSig):
            self.linePlotList[ii].setData(time, signal[:,ii], pen=mypen)
            self.linePlotList[ii+nSig].show()
        # hide extra lines
        for ii in np.arange(self.maxNLine - nSig):
            self.linePlotList[ii+nSig].hide()

        self.graph.setUpdatesEnabled(True)

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

        















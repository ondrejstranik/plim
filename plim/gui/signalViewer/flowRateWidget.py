'''
class for viewing signals from spots' plasmon resonance
'''

import napari
import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QLabel, QSizePolicy,QWidget, QApplication, QVBoxLayout
from qtpy import QtCore
from qtpy.QtCore import Qt, Signal
from magicgui import magicgui

import numpy as np
from plim.algorithm.flowData import FlowData


class FlowRateWidget(QWidget):
    ''' main class for viewing flow rates of the pump channel'''
    DEFAULT = {'nameGUI':'FlowRate',
               'maxNLine': 4, # maxNLine ... max number of line plotted in the gra
            }

    sigSetEvalTime = Signal(float)
    sigSetDTime = Signal(float)

    def __init__(self,signal=None, time= None, flowData=None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        if flowData is not None: self.flowData= flowData
        else:
            self.flowData = FlowData(signal,time)

        self.linePlotList = []
        self.vLine = []
        self.maxNLine = FlowRateWidget.DEFAULT['maxNLine']

        # define position of mouse on the graph - used for the vLine keyboard shortcuts
        self.mousePoint = QtCore.QPointF()

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
        # add vertical lines (mirroring the first two of SignalWidget)
        vLineColor = ['g','r']
        for c in vLineColor:
            vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(c, width=0, style=Qt.SolidLine), pos=0)
            self.graph.addItem(vLine, ignoreBounds=True)
            self.vLine.append(vLine)
        # pre allocate lines for the graph
        for ii in range(self.maxNLine):
            self.linePlotList.append(self.graph.plot())
            self.linePlotList[-1].hide()

        self.graph.scene().sigMouseMoved.connect(self.mouse_moved)

        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        self.setLayout(layout)

    def mouse_moved(self, pos):
        self.mousePoint = self.graph.plotItem.vb.mapSceneToView(pos)

    def keyPressEvent(self, evt):
        ''' request a change of the vLine position, same keys as in SignalWidget '''
        if self.graph.underMouse():
            _text = evt.text()

            if _text == '1':
                self.sigSetEvalTime.emit(self.mousePoint.x())

            if _text == '2':
                self.sigSetDTime.emit(self.mousePoint.x())

        # keep the keyPressEvent on this widget
        self.setFocus()

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
            self.linePlotList[ii].show()
        # hide extra lines
        for ii in np.arange(self.maxNLine - nSig):
            self.linePlotList[ii+nSig].hide()

        self.graph.setUpdatesEnabled(True)

    def setData(self, signal,time=None):
        ''' set the data '''
        self.flowData.setData(signal,time)
        self.drawGraph()

    def addDataValue(self,valueVector,time):
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

        















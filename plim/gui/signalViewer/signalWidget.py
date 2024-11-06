'''
class for viewing signals from spots' plasmon resonance
'''

import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget,QVBoxLayout
from qtpy import QtCore
from magicgui import magicgui

import numpy as np
from plim.algorithm.spotData import SpotData
from plim.algorithm.spotInfo import SpotInfo


class SignalWidget(QWidget):
    ''' main class for viewing signal'''
    DEFAULT = {'nameGUI':'Signal'}

    def __init__(self,signal=None, time= None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        self.sD = SpotData(signal,time)
        self.sI = SpotInfo()

        self.align = False
        self.lineIndex = 0
      

        #define position of mouse on the graph - use for selection
        self.mousePoint = QtCore.QPointF()

        # set this gui of this class
        SignalWidget._setWidget(self)

        self.drawGraph()

    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(auto_call=True, layout='horizontal',
                  alignTime ={'min':0,'max':1e6},
                  range = {'min':0,'max':1e6})
        def fitParameter(
                align: bool = self.align,
                alignTime: float = self.sD.alignTime,
                range: float = self.sD.range):

            self.align= align
            self.sD.setOffset(alignTime,range)
            self.sD.getDSignal() # recalculate in the case the range changed

            self.drawGraph()

        @magicgui(call_button=False,
                  acquisitionTime = {'label':'acquisition Time',
                                     'widget_type': 'Label'} )
        def infoBox(acquisitionTime = 0):
            self.infoBox.acquisitionTime.value = acquisitionTime
        
        @magicgui(auto_call=True, layout='horizontal')
        def lineParameter(
                lineIndex: int = self.lineIndex,
                evalTime: float = self.sD.evalTime,
                dTime: float = self.sD.dTime):
            
            self.lineIndex = lineIndex
            self.sD.getDSignal(evalTime,dTime)
            self.drawGraph()

        @magicgui(call_button=False,layout='horizontal',
                  dSignal = {'label':'dSignal',
                                     'widget_type': 'Label'})
        def infoLine(dSignal = 0):
            self.infoLine.dSignal.value = dSignal
            
        # add graph
        self.graph = pg.plot()
        self.graph.setTitle(f'Peak Position')
        styles = {'color':'r', 'font-size':'20px'}
        self.graph.setLabel('left', 'Position', units='nm')
        self.graph.setLabel('bottom', 'time', units= 's')
        self.graph.scene().sigMouseMoved.connect(self.mouse_moved)

        # fit parameter
        self.fitParameter = fitParameter
        self.infoBox = infoBox
        self.infoLine = infoLine
        self.lineParameter = lineParameter

        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        layout.addWidget(self.infoBox.native)
        layout.addWidget(self.fitParameter.native)
        layout.addWidget(self.lineParameter.native)
        layout.addWidget(self.infoLine.native)

        self.setLayout(layout)

    def mouse_moved(self, pos):
        self.mousePoint =  self.graph.plotItem.vb.mapSceneToView(pos)

    def keyPressEvent(self, evt):
        if self.graph.underMouse():
            _key = evt.key()
            _text = evt.text()

            if _text == 'a':
                self.fitParameter.alignTime.value = self.mousePoint.x()
            
            if _text == 's':
                self._findLine(self.mousePoint.x(),self.mousePoint.y())
                self.lineParameter.lineIndex.value = self.lineIndex

            if _text == '1':
                self.lineParameter.evalTime.value = self.mousePoint.x()

            if _text == '2':
                self.lineParameter.dTime.value = self.sD.evalTime - self.mousePoint.x()





        # keep the keyPressEvent on the this signal widget
        self.setFocus()

    def _findLine(self,x,y):
        ''' find the closest line from the cursor'''

        # TODO: count for the aligment!!
        nx = np.argmin(np.abs(self.sD.time - x))

        offSet = self.sD.offset
        if not self.align:
            offSet = 0*offSet

        self.lineIndex = np.argmin(np.abs(self.sD.signal[nx,:]-offSet -y))

        return self.lineIndex

    def drawGraph(self):
        ''' draw all new lines in the spectraGraph '''

        (signal, time) = self.sD.getData()

        # if there is no signal then do not continue
        if signal is None:
            return

        # remove all lines
        self.graph.clear()

        offSet = self.sD.offset
        if not self.align:
            offSet = 0*offSet

        #try:
            # draw lines
        for ii in np.arange(signal.shape[1]):

            mypen = QPen()
            mypen.setColor(QColor("White"))
            mypen.setWidth(0)
            if ii == self.lineIndex:
                mypen.setStyle(2)

            try:
                mypen.color = QColor.fromRgbF(*list(
                    self.sD.signalColor[ii]))
                lineplot = self.graph.plot(pen= mypen)
            except:
                lineplot = self.graph.plot(pen= mypen)
                print('error occurred in drawGraph - signalWidget')
                print(f'sD.signalColor {self.sD.signalColor}')

            lineplot.setData(time, signal[:,ii]-offSet[ii])
        #except:
        #    print('error occurred in drawSpectraGraph - pointSpectra')

        # display delta time
        if len(time) >1:
            self.infoBox(time[-1] - time[-2])

    def setData(self, signal,time=None):
        ''' set the data '''
        self.sD.setData(signal,time)
        self.drawGraph()

    def addDataValue(self,valueVector,time):
        ''' add new value '''        
        self.sD.addDataValue(valueVector,time)
        self.drawGraph()


if __name__ == "__main__":
    pass

        















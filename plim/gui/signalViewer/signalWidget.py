'''
class for viewing signals from spots' plasmon resonance
'''

import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget,QVBoxLayout
from qtpy import QtCore
from magicgui import magicgui
from qtpy.QtCore import Signal

import numpy as np
from plim.algorithm.spotData import SpotData


class SignalWidget(QWidget):
    ''' main class for viewing signal'''
    DEFAULT = {'nameGUI':'Signal'}
    sigUpdateData = Signal()

    def __init__(self,signal=None, time= None, spotData = None,  **kwargs):
        ''' initialise the class '''
        super().__init__()

        if spotData is not None: self.sD = spotData 
        else:
            if signal is not None: self.sD = SpotData(signal,time)
            else:
                self.sD = SpotData(np.arange(10*3).reshape(10,3))

        self.align = False
        self.lineIndex = 0
      

        #define position of mouse on the graph - use for selection
        self.mousePoint = QtCore.QPointF()

        # set this gui of this class
        SignalWidget._setWidget(self)

        # set the values and graph lines in the gui
        self.lineParameter()

    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(auto_call=True, layout='horizontal',
                  alignTime ={'min':0,'max':1e6, 'tooltip': " to select \n press 'a' on graph"},
                  range = {'min':0,'max':1e6})
        def fitParameter(
                align: bool = self.align,
                alignTime: float = self.sD.alignTime,
                range: int = self.sD.range):

            self.align= align
            self.sD.setOffset(alignTime,range)
            self.sD.getDSignal() # recalculate in the case the range changed
            self.sD.getNoise()
            self.lineParameter.noise.value =  f"{self.sD.noise[self.lineIndex]:.2E}"

            self.drawGraph()

            # emit signal to eventually update data in other guis
            self.sigUpdateData.emit()

        @magicgui(call_button=False,
                  acquisitionTime = {'label':'acquisition Time',
                                     'widget_type': 'Label'} )
        def infoBox(acquisitionTime = 0):
            self.infoBox.acquisitionTime.value = acquisitionTime
        
        @magicgui(auto_call=True, layout='horizontal',
                  lineIndex = {'tooltip': " to select \n press 's' on graph"},
                  evalTime = {'min':0,'max':1e6,'tooltip': " to select \n press '1' on graph"},
                  dTime = {'min':0,'max':1e6,'tooltip': " to select \n press '2' on graph"},
                  dSignal = {'label':'dSignal','widget_type': 'Label'},
                  noise = {'label':'Noise','widget_type': 'Label'},
                  lineVisible = {'tooltip':"to toggle \n press 'v' on graph",
                                 'label':'visible'},
                  lineColor = {'tooltip':"use format #000000 - #FFFFFF",
                                 'label':'color:'},                                 
                  lineName = {'label':'name'}
                  )
        def lineParameter(
                lineIndex: int = self.lineIndex,
                lineName: str = self.sD.table['name'][self.lineIndex],
                lineVisible: bool = self.sD.table['visible'][self.lineIndex]=='True',
                lineColor: str = self.sD.table['color'][self.lineIndex],
                evalTime: float = self.sD.evalTime,
                dTime: float = self.sD.dTime,
                dSignal = None,
                noise = None):

            # line index out of range
            if lineIndex >= len(self.sD.table['name']):
                lineIndex = len(self.sD.table['name'])-1
                self.lineParameter._auto_call = False
                self.lineParameter.lineIndex.value = lineIndex
                self.lineParameter._auto_call = True
                print('index out of line')

            # line index is changed
            if self.lineIndex != lineIndex:
                # change of the line focus
                self.lineIndex = lineIndex

                # recalculate the dSignal and noise
                self.sD.getDSignal()
                self.sD.getNoise()

                # set the display values
                self.lineParameter._auto_call = False
                self.lineParameter.dSignal.value = f"{self.sD.dSignal[lineIndex]:.2E}"
                self.lineParameter.lineVisible.value =  self.sD.table['visible'][lineIndex]=='True'
                self.lineParameter.lineName.value =  self.sD.table['name'][lineIndex]
                self.lineParameter.lineColor.value =  self.sD.table['color'][lineIndex]
                self.lineParameter.noise.value =  f"{self.sD.noise[lineIndex]:.2E}"
                self.lineParameter._auto_call = True
                self.drawGraph()
                print('change of index')

            # visibility is changed
            elif (self.sD.table['visible'][lineIndex]=='True') != lineVisible:
                if lineVisible:
                    self.sD.table['visible'][lineIndex]='True'
                else:
                    self.sD.table['visible'][lineIndex]='False'
                self.drawGraph()
                print('change of visibility')


            # color is changed            
            elif self.sD.table['color'][lineIndex] != lineColor:
                self.sD.table['color'][lineIndex] = lineColor
                self.drawGraph()
                print('change of color')


            # name is changed            
            elif self.sD.table['name'][lineIndex] != lineName:
                self.sD.table['name'][lineIndex] = lineName
                print('change of name')


            # evaluation time or delta time is changed
            elif  (evalTime != self.sD.evalTime) or (dTime != self.sD.dTime):
                self.sD.getDSignal(evalTime,dTime)
                self.sD.getNoise()
                self.lineParameter.dSignal.value = f"{self.sD.dSignal[self.lineIndex]:.2E}"
                self.lineParameter.noise.value =  f"{self.sD.noise[self.lineIndex]:.2E}"
                self.drawGraph()
                print('change of evaluation')


            # emit signal to eventually update data in other guis
            self.sigUpdateData.emit()
            
        # add graph
        self.graph = pg.plot()
        self.graph.setTitle(f'Peak Position')
        styles = {'color':'r', 'font-size':'20px'}
        self.graph.setLabel('left', 'Position', units='nm')
        self.graph.setLabel('bottom', 'time', units= 's')
        self.graph.scene().sigMouseMoved.connect(self.mouse_moved)

        # widgets
        self.fitParameter = fitParameter
        self.infoBox = infoBox
        self.lineParameter = lineParameter

        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        layout.addWidget(self.infoBox.native)
        layout.addWidget(self.fitParameter.native)
        layout.addWidget(self.lineParameter.native)
        self.setLayout(layout)

        self.drawGraph()


    def mouse_moved(self, pos):
        self.mousePoint =  self.graph.plotItem.vb.mapSceneToView(pos)

    def keyPressEvent(self, evt):
        if self.graph.underMouse():
            _key = evt.key()
            _text = evt.text()

            if _text == 'a':
                self.fitParameter.alignTime.value = self.mousePoint.x()
            
            if _text == 's':
                lineIndex = self._findLine(self.mousePoint.x(),self.mousePoint.y())
                self.lineParameter.lineIndex.value = lineIndex

            if _text == '1':
                self.lineParameter.evalTime.value = self.mousePoint.x()

            if _text == '2':
                _value = self.mousePoint.x() - self.sD.evalTime
                if _value < 0 : _value = 0 
                self.lineParameter.dTime.value = _value

            if _text == 'v':
                self.lineParameter.lineVisible.value = not self.lineParameter.lineVisible.value


        # keep the keyPressEvent on the this signal widget
        self.setFocus()

    def _findLine(self,x,y):
        ''' find the closest line from the cursor'''

        nx = np.argmin(np.abs(self.sD.time -self.sD.time0 - x))
        print(f'selection at time {self.sD.time[nx]-self.sD.time0}')

        offSet = self.sD.offset
        if not self.align:
            offSet = 0*offSet

        # remove the one not visible
        _signal = self.sD.signal[nx,:]
        _selection = [ x  != 'True' for x in self.sD.table['visible']]
        _signal[_selection] = np.inf

        print(f'signal {_signal -offSet -y}')

        lineIndex = np.argmin(np.abs(_signal -offSet -y))


        return lineIndex

    def drawGraph(self):
        ''' draw all new lines in the spectraGraph '''

        (signal, time) = self.sD.getData()

        #print(f'signal shape = {signal.shape}')
        #print(f'time shape = {time.shape}')

        # if there is no signal then do not continue
        if signal is None:
            return

        # remove all lines
        self.graph.clear()

        # set off set for the lines
        offSet = self.sD.offset
        if not self.align:
            offSet = np.zeros(signal.shape[1])

        #try:
            # draw lines
        for ii in np.arange(signal.shape[1]):

            try: # TODO: correct for it
                if self.sD.table['visible'][ii] != 'True':
                    continue
            except:
                print('sd table visible not defined')

            mypen = QPen()
            mypen.setColor(QColor("White"))
            mypen.setWidth(0)
            if ii == self.lineIndex:
                mypen.setStyle(2)


            hexColor = self.sD.table['color'][ii]
            rgbaColor = [int(hexColor[1:3],16)/255,
                            int(hexColor[3:5],16)/255,
                            int(hexColor[5:7],16)/255,
                            1]
            mypen.setColor(QColor.fromRgbF(*list(rgbaColor)))
            lineplot = self.graph.plot(pen= mypen)

            '''
            try:
                hexColor = self.sD.table['color'][ii]
                rgbaColor = [int(hexColor[1:3],16)/255,
                              int(hexColor[3:5],16)/255,
                              int(hexColor[5:7],16)/255,
                              1]
                mypen.setColor(QColor.fromRgbF(*list(rgbaColor)))
                lineplot = self.graph.plot(pen= mypen)
            except:
                lineplot = self.graph.plot(pen= mypen)
                print('error occurred in drawGraph - signalWidget')
                print(f"sD.signalColor {self.sD.table['color']}")
            '''
            # TODO: temporarly changed
            lineplot.setData(time, signal[:,ii]-offSet[ii])
            #print(f'offset for line  {ii} is  {offSet[ii]}')

        #except:
        #    print('error occurred in drawSpectraGraph - pointSpectra')

        # display infinity lines
        vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('g', width=0, style=QtCore.Qt.SolidLine))
        vLine.setPos(self.sD.evalTime)
        self.graph.addItem(vLine, ignoreBounds=True)
        vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('r', width=0, style=QtCore.Qt.SolidLine))
        vLine.setPos(self.sD.evalTime+self.sD.dTime)
        self.graph.addItem(vLine, ignoreBounds=True)

        # display infinity lines -  aliment
        if self.align:
            vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('b', width=0, style=QtCore.Qt.SolidLine))
            vLine.setPos(self.sD.alignTime)
            self.graph.addItem(vLine, ignoreBounds=True)

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

    def redrawWidget(self):
        ''' update and redraw the complete widget according the class values'''
        # line parameter Widget
        self.lineParameter._auto_call = False
        self.lineParameter.lineIndex.value = self.lineIndex
        self.lineParameter.dSignal.value = f"{self.sD.dSignal[self.lineIndex]:.2E}"
        self.lineParameter.lineVisible.value =  self.sD.table['visible'][self.lineIndex]=='True'
        self.lineParameter.lineName.value =  self.sD.table['name'][self.lineIndex]
        self.lineParameter.lineColor.value =  self.sD.table['color'][self.lineIndex]
        self.lineParameter.noise.value =  f"{self.sD.noise[self.lineIndex]:.2E}"
        self.lineParameter._auto_call = True        

        # fit parameter widget
        self.fitParameter._auto_call = False
        self.fitParameter.align.value = self.align
        self.fitParameter.alignTime.value = self.sD.alignTime
        self.fitParameter.range.value = self.sD.range
        self.fitParameter._auto_call = True

        # graph widget
        self.drawGraph()

if __name__ == "__main__":
    pass

        






#%%








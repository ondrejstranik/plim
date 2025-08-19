'''
class for viewing signals and their Fits
'''

import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget,QVBoxLayout, QFileDialog
from qtpy import QtCore
from magicgui import magicgui
from plim.gui.signalViewer.signalWidget import SignalWidget
from pathlib import Path

import numpy as np
from plim.algorithm.kineticFit import KineticFit


class FitWidget(QWidget):
    ''' main class for viewing fit of an signal'''
    DEFAULT = {'nameGUI':'Fit'}

    def __init__(self,signal=None, time= None, kineticFit = None,  **kwargs):
        ''' initialise the class '''
        super().__init__()

        if kineticFit is not None: self.kF = kineticFit
        else:
            self.kF = KineticFit()
            if signal is not None: self.kF.setSignal(signal)
            if time is not None: self.kF.setTime(time)


        self.dataObject = None

        # set this gui of this class
        FitWidget._setWidget(self)


    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(layout='horizontal', call_button='fit',
                  time0 = {'max':1e6},
                  tau= {'max':1e6})
        def fitParameter(
                time0: float = 0.0,
                tau: float = 1.0,
                amp: float = 1.0):

            self.kF.setFitParameter(time0=time0)
            self.kF.setFitParameter(tau=tau)
            self.kF.setFitParameter(amp=amp)

            self.kF.calculateFit()

            self.drawGraph()
            #self.infoBox((1/self.kF.fitParam[:,2]).mean(), (1/self.kF.fitParam[:,2]).std())
            self.infoBox(self.kF.fitParam[:,2].mean(), self.kF.fitParam[:,2].std())

            print('fiting the data')

        @magicgui(layout='horizontal', call_button=False,
                  tau = {'label':'tau','widget_type': 'Label'},
                  std = {'label':'std','widget_type': 'Label'} )
        def infoBox(tau = 0, std= 0):
            self.infoBox.tau.value = tau
            self.infoBox.std.value = std

        @magicgui(call_button='transfer data')
        def dataBox():
            if isinstance(self.dataObject, SignalWidget):

                (signal, time) = self.dataObject.sD.getData()
                self.kF
                if not self.dataObject.align:
                    offSet = np.zeros(signal.shape[1])
                else:
                    offSet = self.dataObject.sD.offset
                signal = signal - offSet

                _vis = np.array([True if ii=='True' else False for ii in self.dataObject.sD.table['visible']])
                signal = signal[:,_vis]

                timeMask = ((time>self.dataObject.sD.evalTime) & 
                            (time<(self.dataObject.sD.evalTime + self.dataObject.sD.dTime)))

                table = {'name': [self.dataObject.sD.table["name"][ii] for ii in range(len(_vis)) if _vis[ii]==True]}


                self.setData(signal[timeMask,:],time[timeMask],table=table)

                self.drawGraph(onlyData=True)

        @magicgui(call_button='save fit')
        def saveBox():
            dialog = QFileDialog(self)
            dialog.setDirectory(__file__)
            file = None
            if dialog.exec():
                file = dialog.selectedFiles()

            if file is not None:
                myPath = Path(file[0])
                self.kF.saveFitInfo(str(myPath.parent), str(myPath.name))
                print('fit info exported')


        # add graph
        self.graph = pg.PlotWidget()
        self.graph.setTitle(f'Fits')
        self.graph.setLabel('left', 'Signal', units='nm')
        self.graph.setLabel('bottom', 'time', units= 's')

        # widgets
        self.fitParameter = fitParameter
        self.infoBox = infoBox
        self.dataBox = dataBox
        self.saveBox = saveBox

        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        layout.addWidget(self.dataBox.native)
        layout.addWidget(self.infoBox.native)
        layout.addWidget(self.fitParameter.native)
        layout.addWidget(self.saveBox.native)
        self.setLayout(layout)

    def drawGraph(self, onlyData=False):
        ''' draw all new lines in the spectraGraph '''

        # remove all lines
        self.graph.clear()


        mypen2 = QPen()
        mypen2.setWidth(0)        

        mypen3 = QPen()
        mypen3.setWidth(0)        


        for ii in range(self.kF.signal.shape[1]):
            mypen = QPen()
            mypen.setWidth(0)
            mypen.setColor(QColor("White"))
            mypen.setStyle(1)
            #lineplot = self.graph.plot(pen=mypen)
            #lineplot.setData(self.kF.time,self.kF.signal[:,ii])
            self.graph.plot(self.kF.time,self.kF.signal[:,ii],pen=mypen)

            if onlyData: continue

            mypen = QPen()
            mypen.setWidth(0)        
            mypen.setColor(QColor("Yellow"))
            #lineplot = self.graph.plot(pen=mypen)
            mypen.setStyle(2)
            #lineplot.setData(self.kF.time,
            #                 self.kF.bcgFunction(self.kF.time,*self.kF.fitParam[ii,-2:]))
            self.graph.plot(self.kF.time,
                             self.kF.bcgFunction(self.kF.time,*self.kF.fitParam[ii,-2:]),
                              pen=mypen)
            mypen = QPen()
            mypen.setWidth(0)        
            mypen.setColor(QColor("Red"))
            mypen.setStyle(1)
            #lineplot = self.graph.plot(pen=mypen)
            #lineplot.setData(self.kF.time,
            #                 self.kF.fitFunction(self.kF.time,*self.kF.fitParam[ii,:]))
            self.graph.plot(self.kF.time,
                             self.kF.fitFunction(self.kF.time,*self.kF.fitParam[ii,:]),
                             pen= mypen)



    def connectDataObject(self,dataObject=None):
        ''' connect data from signal Widget'''
        self.dataObject = dataObject

    def setData(self, signal,time,table=None):
        ''' set the data '''
        self.kF.setSignal(signal)
        self.kF.setTime(time)
        self.kF.setTable(table)

if __name__ == "__main__":

    # load data
    from plim.algorithm.fileData import FileData
    from qtpy.QtWidgets import QApplication

    ffile = r'Experiment1'
    ffolder = r'F:\ondra\LPI\25-07-02 dna'

    fData = FileData()
    fData.loadAllFile(ffolder,fileMainName=ffile)    

    fData.spotData.time0 = fData.flowData.time[0]
    fData.spotData.setOffset(alignTime=700, range=5)
    time = fData.spotData.time-fData.spotData.time0

    idx = np.array((68,58,50,40,34))
    sig = fData.spotData.signal[:,idx]-fData.spotData.offset[idx]

    fTime = np.array([200,1800])
    fTimeMask = (time>fTime[0]) & (time<fTime[1])
  
    app = QApplication([])

    fW = FitWidget()
    fW.setData(signal=sig[fTimeMask,:],time=time[fTimeMask])
    fW.fitParameter.time0.value = 700
    fW.fitParameter.tau.value = 300
    fW.fitParameter.amp.value = 1

    fW.show()
    app.exec()

if __name__ == "__main__":
    pass



#%%








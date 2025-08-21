'''
class for viewing signals and their Fits
'''

import pyqtgraph as pg
import pyqtgraph.exporters
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

        # instance from where signal and time can be obtained
        self.dataObject = None

        # set this gui of this class
        FitWidget._setWidget(self)


    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(layout='horizontal', call_button='fit',
                  time0 = {'max':1e6},
                  tau= {'max':1e6},
                  p1 = {'step': 1e-6},
                  varyTime0 = {'label':' '},
                  varyTau = {'label':' '},

                   )
        def fitParameter(
                time0: float = 0.0, varyTime0 = True,
                tau: float = 1.0, varyTau = True,
                amp: float = 1.0, varyAmp = True,
                p0: float = 0.0, varyP0 = True,
                p1: float = 0.0, varyP1 = True):

            self.kF.setFitParameter(name='time0',value=time0,fixed=~varyTime0)
            self.kF.setFitParameter(name='tau',value=tau,fixed=~varyTau)
            self.kF.setFitParameter(name='amp',value=amp,fixed=~varyAmp)
            self.kF.setFitParameter(name='p0',value=p0,fixed=~varyP0)
            self.kF.setFitParameter(name='p1',value=p1,fixed=~varyP1)

            self.kF.calculateFit()

            self.drawGraph()
            #self.infoBox((1/self.kF.fitParam[:,2]).mean(), (1/self.kF.fitParam[:,2]).std())
            self.infoBox(self.kF.fittedParam[:,2].mean(), self.kF.fittedParam[:,2].std(),
                         self.kF.fittedParam[:,-1].mean(), self.kF.fittedParam[:,-1].std())

            print('fitting the data')

        @magicgui(layout='horizontal', call_button=False,
                  tau = {'label':'tau','widget_type': 'Label'},
                  stdTau = {'label':'std','widget_type': 'Label'},
                  drift = {'label':'drift','widget_type': 'Label'},
                  stdDrift = {'label':'std','widget_type': 'Label'}  )
        def infoBox(tau = 0, stdTau= 0, drift=0, stdDrift=0):
            self.infoBox.tau.value = tau
            self.infoBox.stdTau.value = stdTau
            self.infoBox.drift.value = drift
            self.infoBox.stdDrift.value = stdDrift



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

                # save signal graph
                exporter = pyqtgraph.exporters.ImageExporter(self.graph.plotItem)
                # set export parameters if needed
                #exporter.parameters()['width'] = 100   # (note this also affects height parameter)
                exporter.export(str(myPath.parent /myPath.name)  +r"_graph.png")
                print('fit graph exported')




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
                             self.kF.getFittedBackground(idx = ii),
                              pen=mypen)
            mypen = QPen()
            mypen.setWidth(0)        
            mypen.setColor(QColor("Red"))
            mypen.setStyle(1)
            lineplot = self.graph.plot(pen=mypen)
            #lineplot.setData(self.kF.time,
            #                 self.kF.fitFunction(self.kF.time,*self.kF.fitParam[ii,:]))
            self.graph.plot(self.kF.time,
                             self.kF.getFittedSignal(idx=ii),
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
    pass









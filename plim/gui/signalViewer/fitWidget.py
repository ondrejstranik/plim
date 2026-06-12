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
                  p0 = {'step': 1e-2,'min':-10,'max':10},
                  p1 = {'step': 1e-6,'min':-1,'max':1},
                  varyTime0 = {'label':'fixed'},
                  fixTau = {'label':'fixed'},
                  fixAmp = {'label':'fixed'},
                  fixP0 = {'label':'fixed'},
                  fixP1 = {'label':'fixed'}
                   )
        def fitParameter(
                time0: float = 0.0, varyTime0 = False,
                tau: float = 1.0, fixTau = False,
                amp: float = 1.0, fixAmp = False,
                p0: float = 0.0, fixP0 = False,
                p1: float = 0.0, fixP1 = False):

            self.kF.setFitParameter(name='time0',value=time0,fixed=varyTime0)
            self.kF.setFitParameter(name='tau',value=tau,fixed=fixTau, min=0)
            self.kF.setFitParameter(name='amp',value=amp,fixed=fixAmp,min=0)
            self.kF.setFitParameter(name='p0',value=p0,fixed=fixP0)
            self.kF.setFitParameter(name='p1',value=p1,fixed=fixP1)

            self.kF.calculateFit()

            self.drawGraph()

            # TODO: it assumes the adsorption kinetic fit

            self.infoBox(tau= self.kF.fittedParam[:,1].mean(),
                         stdTau= self.kF.fittedParam[:,1].std(),
                         amp= self.kF.fittedParam[:,2].mean(),
                         stdAmp= self.kF.fittedParam[:,2].std(),
                         drift= self.kF.fittedParam[:,4].mean(),
                         stdDrift= self.kF.fittedParam[:,4].std(),
            )
            print('fitted the data')

            print(f'fitted parameters {self.kF.fittedParam}')


        @magicgui(layout='horizontal', call_button=False,
                  tau = {'label':'tau','widget_type': 'Label'},
                  amp = {'label':'amp','widget_type': 'Label'},
                  drift = {'label':'drift','widget_type': 'Label'},
                  stdTau = {'label':' ','widget_type': 'Label'},
                  stdAmp = {'label':' ','widget_type': 'Label'},
                  stdDrift = {'label':' ','widget_type': 'Label'},
        )
        def infoBox(tau = 0, stdTau= '', amp=0, stdAmp='', drift=0, stdDrift=''):
            self.infoBox.tau.value = f'{tau:.1f} ± {stdTau:.1f} s' 
            self.infoBox.amp.value = f'{amp*1000:.1f} ± {stdAmp*1000:.1f} pm' 
            self.infoBox.drift.value = f'{drift*1000*60:.1f} ± {stdDrift*1000*60:.1f} pm/min' 



        @magicgui(call_button='transfer data')
        def dataBox(average:bool = False):
            # if data are transferred from signal widget
            if isinstance(self.dataObject, SignalWidget):

                # get the data from signal widget (aligned and referenced if applied)
                (signal, time) = self.dataObject.sD.getProcessedData()
                #self.kF

                # select only visible
                _vis = np.array([True if ii=='True' else False for ii in self.dataObject.sD.table['visible']])
                signal = signal[:,_vis]

                # select only visible range 
                timeMask = ((time>self.dataObject.sD.evalTime) & 
                            (time<(self.dataObject.sD.evalTime + self.dataObject.sD.dTime)))

                # copy the name only 
                table = {'name': [self.dataObject.sD.table["name"][ii] for ii in range(len(_vis)) if _vis[ii]==True]}

                if average:
                    signal = np.mean(signal,axis=1)[:,None]
                    table = {'name': table['name'][0]}

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
                self.kF.saveFitInfo(str(myPath.parent), str(myPath.name)+r"_data.txt")
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









'''
class for viewing signals and their Fits
'''

import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QTabWidget, QTableWidget, QTableWidgetItem, QShortcut, QApplication, QPushButton
from qtpy.QtGui import QKeySequence
from qtpy import QtCore
from magicgui import magicgui
from plim.gui.signalViewer.signalWidget import SignalWidget
from pathlib import Path

import numpy as np
from plim.algorithm.kineticFit import KineticFit, FitType


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
                  tau= {'max':1e6,'min': -1e6},
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

            self.kF.setFitParameter(fitType=FitType.ADSORPTION)
            self.kF.setFitParameter(name='time0',value=time0,fixed=varyTime0)
            self.kF.setFitParameter(name='tau',value=tau,fixed=fixTau, min=0)
            self.kF.setFitParameter(name='amp',value=amp,fixed=fixAmp,min=0)
            self.kF.setFitParameter(name='p0',value=p0,fixed=fixP0)
            self.kF.setFitParameter(name='p1',value=p1,fixed=fixP1)

            self.kF.calculateFit()

            self.drawGraph()
            self.drawCleanGraph()

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

        @magicgui(layout='horizontal', call_button='fit',
                  time0 = {'max':1e6},
                  tau= {'max':1e6,'min': -1e6},
                  p0 = {'step': 1e-2,'min':-10,'max':10},
                  p1 = {'step': 1e-6,'min':-1,'max':1},
                  varyTime0 = {'label':'fixed'},
                  fixTau = {'label':'fixed'},
                  fixAmp = {'label':'fixed'},
                  fixP0 = {'label':'fixed'},
                  fixP1 = {'label':'fixed'}
                   )
        def fitParameter2(
                time0: float = 0.0, varyTime0 = False,
                tau: float = 1.0, fixTau = False,
                amp: float = 1.0, fixAmp = False,
                p0: float = 0.0, fixP0 = False,
                p1: float = 0.0, fixP1 = False):

            self.kF.setFitParameter(fitType=FitType.DESORPTION)
            self.kF.setFitParameter(name='time0',value=time0,fixed=varyTime0)
            self.kF.setFitParameter(name='tau',value=tau,fixed=fixTau, min=0)
            self.kF.setFitParameter(name='amp',value=amp,fixed=fixAmp,min=0)
            self.kF.setFitParameter(name='p0',value=p0,fixed=fixP0)
            self.kF.setFitParameter(name='p1',value=p1,fixed=fixP1)

            self.kF.calculateFit()

            self.drawGraph()
            self.drawCleanGraph()

            self.infoBox2(tau= self.kF.fittedParam[:,1].mean(),
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
        def infoBox2(tau = 0, stdTau= '', amp=0, stdAmp='', drift=0, stdDrift=''):
            self.infoBox2.tau.value = f'{tau:.1f} ± {stdTau:.1f} s' 
            self.infoBox2.amp.value = f'{amp*1000:.1f} ± {stdAmp*1000:.1f} pm' 
            self.infoBox2.drift.value = f'{drift*1000*60:.1f} ± {stdDrift*1000*60:.1f} pm/min'

        @magicgui(layout='horizontal', call_button='fit',
                  time0 = {'max':1e6},
                  slope= {'max':10,'min': -10},
                  p0 = {'step': 1e-2,'min':-10,'max':10},
                  p1 = {'step': 1e-6,'min':-1,'max':1},
                  varyTime0 = {'label':'fixed'},
                  fixSlope = {'label':'fixed'},
                  fixP0 = {'label':'fixed'},
                  fixP1 = {'label':'fixed'}
                   )
        def fitParameter3(
                time0: float = 0.0, varyTime0 = False,
                slope: float = 1.0, fixSlope = False,
                p0: float = 0.0, fixP0 = False,
                p1: float = 0.0, fixP1 = False):

            self.kF.setFitParameter(fitType=FitType.LINEAR)
            self.kF.setFitParameter(name='time0',value=time0,fixed=varyTime0)
            self.kF.setFitParameter(name='slope',value=slope,fixed=fixSlope)
            self.kF.setFitParameter(name='p0',value=p0,fixed=fixP0)
            self.kF.setFitParameter(name='p1',value=p1,fixed=fixP1)

            self.kF.calculateFit()

            self.drawGraph()
            self.drawCleanGraph()

            self.infoBox3(slope= self.kF.fittedParam[:,1].mean(),
                         stdSlope= self.kF.fittedParam[:,1].std(),
                          drift= self.kF.fittedParam[:,3].mean(),
                         stdDrift= self.kF.fittedParam[:,3].std(),
            )
            print('fitted the data')

            print(f'fitted parameters {self.kF.fittedParam}')


        @magicgui(layout='horizontal', call_button=False,
                  slope = {'label':'tau','widget_type': 'Label'},
                  drift = {'label':'drift','widget_type': 'Label'},
                  stdSlope = {'label':' ','widget_type': 'Label'},
                  stdDrift = {'label':' ','widget_type': 'Label'},
        )
        def infoBox3(slope = 0, stdSlope= '', drift=0, stdDrift=''):
            self.infoBox3.slope.value = f'{slope:.1f} ± {stdSlope:.1f} nm/s' 
            self.infoBox3.drift.value = f'{drift*1000*60:.1f} ± {stdDrift*1000*60:.1f} pm/min'

        @magicgui(layout='horizontal', call_button='fit',
                  time0 = {'max':1e6},
                  tau1= {'max':1e6,'min': -1e6},
                  tau2= {'max':1e6,'min': -1e6},
                  p0 = {'step': 1e-2,'min':-10,'max':10},
                  p1 = {'step': 1e-6,'min':-1,'max':1},
                  varyTime0 = {'label':'fixed'},
                  fixTau1 = {'label':'fixed'},
                  fixAmp1 = {'label':'fixed'},
                  fixTau2 = {'label':'fixed'},
                  fixAmp2 = {'label':'fixed'},
                  fixP0 = {'label':'fixed'},
                  fixP1 = {'label':'fixed'}
                   )
        def fitParameter4(
                time0: float = 0.0, varyTime0 = False,
                tau1: float = 10.0, fixTau1 = False,
                amp1: float = 1.0,  fixAmp1 = False,
                tau2: float = 100.0, fixTau2 = False,
                amp2: float = 0.5,  fixAmp2 = False,
                p0: float = 0.0, fixP0 = False,
                p1: float = 0.0, fixP1 = False):

            self.kF.setFitParameter(fitType=FitType.ADSORPTION_DOUBLE)
            self.kF.setFitParameter(name='time0', value=time0, fixed=varyTime0)
            self.kF.setFitParameter(name='tau1',  value=tau1,  fixed=fixTau1, min=0)
            self.kF.setFitParameter(name='amp1',  value=amp1,  fixed=fixAmp1, min=0)
            self.kF.setFitParameter(name='tau2',  value=tau2,  fixed=fixTau2, min=0)
            self.kF.setFitParameter(name='amp2',  value=amp2,  fixed=fixAmp2, min=0)
            self.kF.setFitParameter(name='p0',    value=p0,    fixed=fixP0)
            self.kF.setFitParameter(name='p1',    value=p1,    fixed=fixP1)

            self.kF.calculateFit()
            self.drawGraph()
            self.drawCleanGraph()

            self.infoBox4(
                tau1    = self.kF.fittedParam[:,1].mean(),
                stdTau1 = self.kF.fittedParam[:,1].std(),
                amp1    = self.kF.fittedParam[:,2].mean(),
                stdAmp1 = self.kF.fittedParam[:,2].std(),
                tau2    = self.kF.fittedParam[:,3].mean(),
                stdTau2 = self.kF.fittedParam[:,3].std(),
                amp2    = self.kF.fittedParam[:,4].mean(),
                stdAmp2 = self.kF.fittedParam[:,4].std(),
                drift   = self.kF.fittedParam[:,6].mean(),
                stdDrift= self.kF.fittedParam[:,6].std(),
            )
            print(f'fitted parameters {self.kF.fittedParam}')


        @magicgui(layout='horizontal', call_button=False,
                  tau1    = {'label':'tau1',  'widget_type': 'Label'},
                  stdTau1 = {'label':' ',     'widget_type': 'Label'},
                  amp1    = {'label':'amp1',  'widget_type': 'Label'},
                  stdAmp1 = {'label':' ',     'widget_type': 'Label'},
                  tau2    = {'label':'tau2',  'widget_type': 'Label'},
                  stdTau2 = {'label':' ',     'widget_type': 'Label'},
                  amp2    = {'label':'amp2',  'widget_type': 'Label'},
                  stdAmp2 = {'label':' ',     'widget_type': 'Label'},
                  drift   = {'label':'drift', 'widget_type': 'Label'},
                  stdDrift= {'label':' ',     'widget_type': 'Label'},
        )
        def infoBox4(tau1=0, stdTau1='', amp1=0, stdAmp1='',
                     tau2=0, stdTau2='', amp2=0, stdAmp2='',
                     drift=0, stdDrift=''):
            self.infoBox4.tau1.value    = f'{tau1:.1f} ± {stdTau1:.1f} s'
            self.infoBox4.amp1.value    = f'{amp1*1000:.1f} ± {stdAmp1*1000:.1f} pm'
            self.infoBox4.tau2.value    = f'{tau2:.1f} ± {stdTau2:.1f} s'
            self.infoBox4.amp2.value    = f'{amp2*1000:.1f} ± {stdAmp2*1000:.1f} pm'
            self.infoBox4.drift.value   = f'{drift*1000*60:.1f} ± {stdDrift*1000*60:.1f} pm/min'

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
        self.graph.setLabel('left', 'R signal', units='nm')
        self.graph.setLabel('bottom', 'time', units= 's')

        # parameter table
        self.paramTable = QTableWidget()
        self.paramTable.setEditTriggers(QTableWidget.NoEditTriggers)
        copy_shortcut = QShortcut(QKeySequence.Copy, self.paramTable)
        copy_shortcut.activated.connect(self._copyTableToClipboard)
        self.paramTable.itemSelectionChanged.connect(self.updateStatGraph)

        # stat graph (shown next to the table)
        self.statGraph = pg.PlotWidget()
        self.statGraph.setLabel('bottom', 'curve index')
        self.statGraph.setMaximumWidth(300)

        # widgets
        self.fitParameter = fitParameter
        self.infoBox = infoBox
        self.fitParameter2 = fitParameter2
        self.infoBox2 = infoBox2
        self.fitParameter3 = fitParameter3
        self.infoBox3 = infoBox3
        self.fitParameter4 = fitParameter4
        self.infoBox4 = infoBox4

        self.dataBox = dataBox
        self.saveBox = saveBox

        graphPage = QWidget()
        graphPage_layout = QVBoxLayout()
        graphPage_layout.addWidget(self.graph)
        graphPage_layout.addWidget(self.dataBox.native)
        graphPage.setLayout(graphPage_layout)

        loadBtn = QPushButton("← Use fitted as initial values")
        loadBtn.clicked.connect(self.loadFittedToInitial)

        tableRow = QHBoxLayout()
        tableRow.addWidget(self.paramTable, stretch=3)
        tableRow.addWidget(self.statGraph,  stretch=1)

        paramPage = QWidget()
        paramPage_layout = QVBoxLayout()
        paramPage_layout.addLayout(tableRow)
        paramPage_layout.addWidget(loadBtn)
        paramPage_layout.addWidget(self.saveBox.native)
        paramPage.setLayout(paramPage_layout)

        self.cleanGraph = pg.PlotWidget()
        self.cleanGraph.setTitle('Background subtracted')
        self.cleanGraph.setLabel('left', 'R signal', units='nm')
        self.cleanGraph.setLabel('bottom', 'time', units='s')

        self.viewTab = QTabWidget()
        self.viewTab.addTab(graphPage,          "Graph")
        self.viewTab.addTab(paramPage,          "Parameters")
        self.viewTab.addTab(self.cleanGraph,    "Clean")

        layout = QVBoxLayout()
        layout.addWidget(self.viewTab)

        tab_widget = QTabWidget()

        tab1 = QWidget()
        tab1_layout = QVBoxLayout()
        tab1_layout.addWidget(self.infoBox.native)
        tab1_layout.addWidget(self.fitParameter.native)
        tab1.setLayout(tab1_layout)

        tab2 = QWidget()
        tab2_layout = QVBoxLayout()
        tab2_layout.addWidget(self.infoBox2.native)
        tab2_layout.addWidget(self.fitParameter2.native)
        tab2.setLayout(tab2_layout)

        tab3 = QWidget()
        tab3_layout = QVBoxLayout()
        tab3_layout.addWidget(self.infoBox3.native)
        tab3_layout.addWidget(self.fitParameter3.native)
        tab3.setLayout(tab3_layout)

        tab4 = QWidget()
        tab4_layout = QVBoxLayout()
        tab4_layout.addWidget(self.infoBox4.native)
        tab4_layout.addWidget(self.fitParameter4.native)
        tab4.setLayout(tab4_layout)

        tab_widget.addTab(tab1, "binding")
        tab_widget.addTab(tab4, "binding double")
        tab_widget.addTab(tab3, "binding linear")
        tab_widget.addTab(tab2, "desorption")

        layout.addWidget(tab_widget)
        
        self.setLayout(layout)


    @staticmethod
    def _set_value(widget, value):
        try:
            widget.value = value
        except ValueError:
            pass  # value outside widget's allowed range — leave unchanged

    def loadFittedToInitial(self):
        '''Push mean fitted parameter values back into the initial-value spin boxes.'''
        if self.kF.fittedParam is None:
            return
        m = self.kF.fittedParam.mean(axis=0)
        s = self._set_value
        ft = self.kF.fitType
        if ft == FitType.ADSORPTION:
            s(self.fitParameter.time0, m[0])
            s(self.fitParameter.tau,   m[1])
            s(self.fitParameter.amp,   m[2])
            s(self.fitParameter.p0,    m[3])
            s(self.fitParameter.p1,    m[4])
        elif ft == FitType.DESORPTION:
            s(self.fitParameter2.time0, m[0])
            s(self.fitParameter2.tau,   m[1])
            s(self.fitParameter2.amp,   m[2])
            s(self.fitParameter2.p0,    m[3])
            s(self.fitParameter2.p1,    m[4])
        elif ft == FitType.LINEAR:
            s(self.fitParameter3.time0, m[0])
            s(self.fitParameter3.slope, m[1])
            s(self.fitParameter3.p0,    m[2])
            s(self.fitParameter3.p1,    m[3])
        elif ft == FitType.ADSORPTION_DOUBLE:
            s(self.fitParameter4.time0, m[0])
            s(self.fitParameter4.tau1,  m[1])
            s(self.fitParameter4.amp1,  m[2])
            s(self.fitParameter4.tau2,  m[3])
            s(self.fitParameter4.amp2,  m[4])
            s(self.fitParameter4.p0,    m[5])
            s(self.fitParameter4.p1,    m[6])

    def _copyTableToClipboard(self):
        '''Copy selected table cells to the clipboard as tab-separated text.'''
        items = self.paramTable.selectedItems()
        if not items:
            return
        rows = sorted(set(item.row()    for item in items))
        cols = sorted(set(item.column() for item in items))
        lines = []
        for r in rows:
            lines.append('\t'.join(
                (self.paramTable.item(r, c).text() if self.paramTable.item(r, c) else '')
                for c in cols
            ))
        QApplication.clipboard().setText('\n'.join(lines))

    def updateStatGraph(self):
        '''Boxplot of the currently selected table column with all individual points.'''
        self.statGraph.clear()
        cols = sorted(set(item.column() for item in self.paramTable.selectedItems()))
        if not cols:
            return
        col = cols[0]
        header = self.paramTable.horizontalHeaderItem(col)
        param_name = header.text() if header else f'col {col}'

        values = []
        for row in range(self.paramTable.rowCount()):
            item = self.paramTable.item(row, col)
            if item:
                try:
                    values.append(float(item.text()))
                except ValueError:
                    pass
        if not values:
            return

        values = np.array(values)
        n      = len(values)
        q1     = np.percentile(values, 25)
        median = np.percentile(values, 50)
        q3     = np.percentile(values, 75)
        mean   = values.mean()
        std    = values.std()
        iqr    = q3 - q1
        lo     = max(values.min(), q1 - 1.5 * iqr)
        hi     = min(values.max(), q3 + 1.5 * iqr)

        w = 0.25   # half-width of the box

        # IQR box (filled)
        box = pg.BarGraphItem(x=[0], height=[q3 - q1], width=2 * w, y0=q1,
                              brush=pg.mkBrush(100, 150, 255, 80),
                              pen=pg.mkPen((70, 130, 180), width=2))
        self.statGraph.addItem(box)

        # median line (red)
        self.statGraph.plot([-w, w], [median, median],
                            pen=pg.mkPen('r', width=2))

        # mean marker (red diamond)
        self.statGraph.plot([0], [mean], pen=None,
                            symbol='d', symbolSize=10,
                            symbolBrush='r', symbolPen=None)

        # whiskers
        self.statGraph.plot([0, 0], [lo, q1], pen=pg.mkPen('w', width=1))
        self.statGraph.plot([0, 0], [q3, hi], pen=pg.mkPen('w', width=1))

        # whisker caps
        cw = w * 0.5
        self.statGraph.plot([-cw, cw], [lo, lo], pen=pg.mkPen('w', width=1))
        self.statGraph.plot([-cw, cw], [hi, hi], pen=pg.mkPen('w', width=1))

        # all individual data points jittered on x (semi-transparent white)
        rng     = np.random.default_rng(42)
        jitter  = rng.uniform(-w * 0.4, w * 0.4, n)
        scatter = pg.ScatterPlotItem(x=jitter, y=values,
                                     pen=None, brush=pg.mkBrush(255, 255, 255, 160),
                                     size=7)
        self.statGraph.addItem(scatter)

        self.statGraph.setTitle(f'{param_name}:  {mean:.4g} ± {std:.4g}')
        self.statGraph.setLabel('left', param_name)
        self.statGraph.getAxis('bottom').setTicks([[]])
        self.statGraph.setXRange(-0.5, 0.5)

    def updateTable(self):
        '''Populate the Parameters tab with the current fitted values.'''
        if self.kF.fittedParam is None:
            return
        nFit, nParam = self.kF.fittedParam.shape
        param_names = self.kF.fitType.parameters
        self.paramTable.setRowCount(nFit)
        self.paramTable.setColumnCount(nParam)
        self.paramTable.setHorizontalHeaderLabels(param_names)
        names = (self.kF.table or {}).get('name') or [str(i) for i in range(nFit)]
        self.paramTable.setVerticalHeaderLabels([str(n) for n in names])
        def _fmt(v):
            s = f'{v:.6g}'
            return s if ('.' in s or 'e' in s) else s + '.0'

        for i in range(nFit):
            for j in range(nParam):
                self.paramTable.setItem(i, j, QTableWidgetItem(_fmt(self.kF.fittedParam[i, j])))
        self.paramTable.resizeColumnsToContents()

    def drawCleanGraph(self):
        '''Plot background-subtracted signal and fit in the Clean tab.'''
        self.cleanGraph.clear()
        if self.kF.fittedParam is None:
            return
        clean_signal, clean_fit = self.kF.getCleanDataFit()
        for ii in range(clean_signal.shape[1]):
            pen_data = QPen()
            pen_data.setWidth(0)
            pen_data.setColor(QColor('White'))
            self.cleanGraph.plot(self.kF.time, clean_signal[:, ii], pen=pen_data)

            pen_fit = QPen()
            pen_fit.setWidth(0)
            pen_fit.setColor(QColor('Red'))
            self.cleanGraph.plot(self.kF.time, clean_fit[:, ii], pen=pen_fit)

    def drawGraph(self, onlyData=False):
        ''' draw all new lines in the spectraGraph '''

        # remove all lines
        self.graph.clear()
        self.updateTable()


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









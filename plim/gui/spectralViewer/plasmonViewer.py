'''
class for viewing spots's plasmon resonance
'''
import HSIplasmon as hsi
from HSIplasmon.SpectraViewerModel2 import SpectraViewerModel2
from HSIplasmon.algorithm.plasmonpeakfit import (fit_polynom, get_peakmax, get_peakcenter)

import napari
import time
from timeit import default_timer as timer
import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen

from magicgui import magicgui
from enum import Enum
from typing import Annotated, Literal

import numpy as np

#%% TODO: implement plasmonSpectra class in the code
class PlasmonViewer(SpotSpectraViewer):
    ''' main viewer for the plasmon resonances of spots'''

    def __init__(self, xywImage=None, wavelength= None, **kwargs):
        ''' initialise the class '''

        super().__init__(xywImage=xywImage, wavelength= wavelength, **kargs)

        # calculated parameters
        self.fitSpectra = [] # list of fitted spectra
        self.peakPosition = [] # list of plasmon position
        self.wavelengthStartFit = 500
        self.wavelengthStopFit = 650
        self.orderFit = 8
        self.peakWidth = 40
        self.wavelengthGuess = 550

        #gui parameters
        self.lineplotList3 = [] # fit line
        self.lineplotList4 = [] # peak vertical line
        self.lineplotList5 = [] # peak position line
        self.fitParameterGui = None
        self.peakPositionGraph = None

        # run the postInit code
        self.postInit(postInitFlag)


    def _setViewerWidget(self):
        ''' prepare the qui '''

        super()._setViewerWidget()


        # set pyqt
        @magicgui()
        def fitParameterGui(
            wavelengthStart: float = self.wavelengthStartFit,
            wavelengthStop: float = self.wavelengthStopFit,
            orderFit: int = self.orderFit,
            peakWidth: float = self.peakWidth,
            wavelengthGuess: float = self.wavelengthGuess
            ):

            self.wavelengthStartFit = wavelengthStart
            self.wavelengthStopFit = wavelengthStop
            self.orderFit = orderFit
            self.peakWidth =  peakWidth
            self.wavelengthGuess = wavelengthGuess

            self.updateSpectra()


        self.fitParameterGui = fitParameterGui

        # add widget 
        dw = self.viewer.window.add_dock_widget(self.fitParameterGui, name ='fit param', area='bottom')
        if self.dockWidgetParameter is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetParameter,dw)
        self.dockWidgetParameter = dw

        # add widget peakPositionGraph
        self.peakPositionGraph = pg.plot()
        self.peakPositionGraph.setTitle(f'Peak Position')
        styles = {'color':'r', 'font-size':'20px'}
        self.peakPositionGraph.setLabel('left', 'Position', units='nm')
        self.peakPositionGraph.setLabel('bottom', 'time', units= 's')
        dw = self.viewer.window.add_dock_widget( self.peakPositionGraph, name = 'peak position')
        # tabify the widget
        if self.dockWidgetData is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetData,dw)
        self.dockWidgetData = dw

    def setImage(self):
        ''' add the time of recording '''
        super.setImage()
        self.updatePeakPositionGraph()

    def calculateFit(self):
        ''' calculate fits at the given points'''
        
        if self.showRawSpectra == False:

            self.fitSpectra = []
            self.peakPosition = []

            fitfunction = fit_polynom
            ffvar =  {'Np':self.orderFit}
            #peakfun = get_peakmax
            peakfun = get_peakcenter
            pfvar =  {'peakwidth': self.peakWidth, 'ini_guess': self.wavelengthGuess}

            wrange = ((self.wavelength> self.wavelengthStartFit) &
                        (self.wavelength < self.wavelengthStopFit))

            # calculate fits
            for ii in np.arange(len(self.pointSpectra)):
                '''
                try:
                    f = fitfunction(self.wavelength[wrange],self.pointSpectra[ii][wrange],ffvar)
                    #peakPosition = peakfun(f,**pfvar)

                    self.fitSpectra.append(f(self.wavelength[wrange]))
                except:
                    print('calculate fit - failed')
                    self.fitSpectra.append(0*self.wavelength[wrange])
                '''
                # TODO: change pointSpectra to numpy array
                mypointSpectra = np.array(self.pointSpectra[ii])
                f = fitfunction(self.wavelength[wrange],mypointSpectra[wrange],**ffvar)
                self.fitSpectra.append(f(self.wavelength[wrange]))
                self.peakPosition.append(peakfun(f,**pfvar))

    def updateSpectra(self):
        ''' update spectra after the data were changed '''
        self.calculateSpectra()
        # update the mask in napari
        self.maskLayer.data = self.spotSpectra.getMask()
        
        self.calculateFit()
        self.drawSpectraGraph()
        self.drawPeakPositionGraph()

    def drawSpectraGraph(self):
        ''' draw all new lines in the spectraGraph '''
        super().drawSpectraGraph()

        self.lineplotList3 = []
        self.lineplotList4 = []                

        if self.showRawSpectra == False:
            try:
                wrange = ((self.wavelength> self.wavelengthStartFit) &
                            (self.wavelength < self.wavelengthStopFit))

                # fitSpectra
                for ii in np.arange(len(self.fitSpectra)):
                    mypen = QPen(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))
                    mypen.setWidth(0)
                    lineplot = self.spectraGraph.plot(pen= mypen)
                    lineplot.setData(self.wavelength[wrange], self.fitSpectra[ii])
                    self.lineplotList3.append(lineplot)

                    lineplot = self.spectraGraph.addLine(x = self.peakPosition[ii], pen= mypen)
                    self.lineplotList4.append(lineplot)
            except:
                print('error occurred in drawSpectraGraph')                

    def updateSpectraGraph(self):
        ''' update the lines in the spectra graph '''
        super().updateSpectraGraph()

        if self.showRawSpectra == False:

            try:
                wrange = ((self.wavelength> self.wavelengthStartFit) &
                            (self.wavelength < self.wavelengthStopFit))

                # pointSpectra
                for ii in np.arange(len(self.fitSpectra)):
                    myline = self.lineplotList3[ii]
                    mypen = QPen(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))
                    mypen.setWidth(0)
                    myline.setData(self.wavelength[wrange],self.fitSpectra[ii], pen = mypen)

                    self.lineplotList4[ii].setValue(self.peakPosition[ii])
            except:
                print('error occurred in update_spectraGraph - fitSpectra')

    def drawPeakPositionGraph(self):

        self.peakPositionGraph.clear()

        self.lineplotList5 = []

        for ii in np.arange(len(self.peakPosition)):
            mypen = QPen(QColor.fromRgbF(*list(
                self.pointLayer.face_color[ii])))
            mypen.setWidth(0)
            lineplot = self.peakPositionGraph.plot(pen= mypen)
            lineplot.setData([1],
                [self.peakPosition[ii]],
                symbol ='o',
                symbolSize = 14,
                symbolBrush = QColor.fromRgbF(*list(self.pointLayer.face_color[ii])),
                pen= mypen)
            self.lineplotList5.append(lineplot)

    def updatePeakPositionGraph(self):

        for ii in np.arange(len(self.peakPosition)):
            mypen = QPen(QColor.fromRgbF(*list(
                self.pointLayer.face_color[ii])))
            mypen.setWidth(0)
            myline = self.lineplotList5[ii]
            myline.setData([1], [self.peakPosition[ii]],
                symbol ='o',
                symbolSize = 14,
                symbolBrush = QColor.fromRgbF(*list(self.pointLayer.face_color[ii])),
                mypen = pen)


if __name__ == "__main__":
        #im = np.random.rand(10,100,100)
        #wavelength = np.arange(im.shape[0])*1.3+ 10
        
        container = np.load(hsi.dataFolder + '/plasmonicArray.npz')

        sViewer = PlasmonViewer(container['arr_0'], container['arr_1'])
        napari.run()















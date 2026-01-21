'''
class for viewing spots's plasmon resonance
'''
#import HSIplasmon as hsi
#from HSIplasmon.SpectraViewerModel2 import SpectraViewerModel2
#from HSIplasmon.algorithm.plasmonpeakfit import (fit_polynom, get_peakmax, get_peakcenter)

from plim.gui.spectralViewer.spotSpectraViewer import SpotSpectraViewer
from plim.algorithm.plasmonFit import PlasmonFit

import napari
import time
from timeit import default_timer as timer
import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen

from magicgui import magicgui
from enum import Enum
from typing import Annotated, Literal
import traceback

import numpy as np

class PlasmonViewer(SpotSpectraViewer):
    ''' main viewer for the plasmon resonances of spots'''

    def __init__(self, xywImage=None, wavelength= None, **kwargs):
        ''' initialise the class '''

        super().__init__(xywImage=xywImage, wavelength= wavelength, **kwargs)

        # calculated parameters
        self.pF = PlasmonFit(wavelength = wavelength)

        #gui parameters
        self.lineplotList3 = [] # fit line
        self.lineplotList4 = [] # peak vertical line
        self.fitParameterGui = None


        # set gui
        PlasmonViewer._setWidget(self)


    def _setWidget(self):
        ''' prepare the qui '''

        # set pyqt
        @magicgui()
        def fitParameterGui(
            wavelengthStart: float = self.pF.wavelengthStartFit,
            wavelengthStop: float = self.pF.wavelengthStopFit,
            orderFit: int = self.pF.orderFit,
            peakWidth: float = self.pF.peakWidth,
            wavelengthGuess: float = self.pF.wavelengthGuess
            ):

            self.pF.wavelengthStartFit = wavelengthStart
            self.pF.wavelengthStopFit = wavelengthStop
            self.pF.orderFit = orderFit
            self.pF.peakWidth =  peakWidth
            self.pF.wavelengthGuess = wavelengthGuess

            self.updateSpectra()


        # add widget fitParameterGui
        self.fitParameterGui = fitParameterGui
        dw = self.viewer.window.add_dock_widget(self.fitParameterGui, name ='fit param', area='bottom')
        if self.dockWidgetParameter is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetParameter,dw)
        self.dockWidgetParameter = dw

    def calculateSpectra(self):
        ''' calculate the spectra and the fits '''
        super().calculateSpectra()
        self.pF.setSpectra(self.spotSpectra.getA())
        self.pF.calculateFit()

    def setWavelength(self,wavelength):
        ''' set the wavelength '''
        super().setWavelength(wavelength)
        self.pF.setWavelength(wavelength)

    def redraw(self):
        ''' only redraw the images, spectra. It does not recalculate it '''
        self.spectraLayer.data = self.xywImage
        self.updateSpectraGraph()
        self.updateHistogram()



    def drawSpectraGraph(self):
        ''' draw all new lines in the spectraGraph '''
        super().drawSpectraGraph()

        # draw additional fit line and peak position line
        self.lineplotList3 = []
        self.lineplotList4 = []                

        if self.showRawSpectra == False:
            try:
                fitSpectra = self.pF.getFit()
                w = self.pF.getWavelength()
                peakPosition = self.pF.getPosition()
                # fitSpectra
                for ii in np.arange(len(fitSpectra)):
                    mypen = QPen(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))
                    mypen.setWidth(0)
                    lineplot = self.spectraGraph.plot(pen= mypen)
                    # speeding up drawing
                    lineplot = self._speedUpLineDrawing(lineplot)
                    lineplot.setData(w, fitSpectra[ii])
                    self.lineplotList3.append(lineplot)

                    lineplot = self.spectraGraph.addLine(x = peakPosition[ii], pen= mypen)
                    # speeding up drawing
                    #lineplot = self._speedUpLineDrawing(lineplot)
                    self.lineplotList4.append(lineplot)
            except:
                print('error occurred in drawSpectraGraph')                

    def updateSpectraGraph(self):
        ''' update the lines in the spectra graph '''
        super().updateSpectraGraph()

        if self.showRawSpectra == False:
            try:
                fitSpectra = self.pF.getFit()
                w = self.pF.getWavelength()
                peakPosition = self.pF.getPosition()
                # pointSpectra
                for ii in np.arange(len(fitSpectra)):
                    myline = self.lineplotList3[ii]
                    mypen = QPen(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))
                    mypen.setWidth(0)
                    myline.setData(w,fitSpectra[ii], pen = mypen)
                    self.lineplotList4[ii].setValue(peakPosition[ii])
            except:
                print('error occurred in update_spectraGraph - fitSpectra')
                traceback.print_exc()



if __name__ == "__main__":
    pass















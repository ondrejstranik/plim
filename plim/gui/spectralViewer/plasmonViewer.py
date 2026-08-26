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
import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen

from magicgui import magicgui
from enum import Enum
from typing import Annotated, Literal
import logging
from timeit import default_timer as timer

import numpy as np

logger = logging.getLogger(__name__)

class PlasmonViewer(SpotSpectraViewer):
    ''' main viewer for the plasmon resonances of spots'''

    def __init__(self, image=None, wavelength= None, **kwargs):
        ''' initialise the class '''

        super().__init__(image=image, wavelength= wavelength, **kwargs)

        # calculated parameters
        self.pF = PlasmonFit(wavelength = wavelength)

        #gui parameters
        self.linePlotList3 = [] # peak vertical line
        
        # fit gadget
        self.fitParameterGui = None

        # set gui
        PlasmonViewer._setWidget(self)


    def _setWidget(self):
        ''' prepare the qui '''

        # set pyqt
        @magicgui(call_button='Set')
        def fitParameterGui(
            wavelengthStart: float = self.pF.wavelengthStartFit,
            wavelengthStop: float = self.pF.wavelengthStopFit,
            orderFit: int = self.pF.orderFit,
            peakWidth: float = self.pF.peakWidth,
            wavelengthGuess: float = self.pF.wavelengthGuess
            ):

            self.pF.wavelengthStartFit = wavelengthStart
            fitParameterGui.wavelengthStart.value = wavelengthStart
            self.pF.wavelengthStopFit = wavelengthStop
            fitParameterGui.wavelengthStop.value = wavelengthStop
            self.pF.orderFit = orderFit
            fitParameterGui.orderFit.value = orderFit
            self.pF.peakWidth =  peakWidth
            fitParameterGui.peakWidth.value = peakWidth
            self.pF.wavelengthGuess = wavelengthGuess
            fitParameterGui.wavelengthGuess.value = wavelengthGuess

            # recalculate fit and redraw the spectra
            self.calculateSpectra()
            self.redraw(modified='image')


        # add widget fitParameterGui
        self.fitParameterGui = fitParameterGui
        dw = self.viewer.window.add_dock_widget(self.fitParameterGui, name ='fit param', area='bottom')
        if self.dockWidgetParameter is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetParameter,dw)
        self.dockWidgetParameter = dw
        # register the graph in menu
        if self.window_menu is not None:
            self.window_menu.addAction(dw.toggleViewAction())

        # adapt the spectra widget
        # pre allocate extra new lines for the graph
        for ii in range(self.maxNLine):
            self.linePlotList3.append(self.spectraGraph.plot())
            self.linePlotList3[-1].hide()
            self._speedUpLineDrawing(self.linePlotList3[-1])

    def calculateSpectra(self):
        ''' calculate the spectra and the fits '''
        super().calculateSpectra()
        self.pF.setSpectra(self.spotSpectra.getSpectra())
        self.pF.calculateFit()

    def setWavelength(self,wavelength):
        ''' set the wavelength '''
        super().setWavelength(wavelength)
        self.pF.setWavelength(wavelength)

    def drawSpectraGraph(self):
        ''' draw lines in the spectraGraph '''
        super().drawSpectraGraph()

        # if there is no points then do not continue
        try:
            nSig = len(self.spotSpectra.getSpectra())
        except:
            return

        # draw additional fit line and peak position line if it is set up
        if self.showRawSpectra == False:

            self.spectraGraph.setUpdatesEnabled(False)

            fitSpectra = self.pF.getFit()
            w = self.pF.getWavelength()
            fitPeak = self.pF.getFitPeak()
            # loop over all points
            for ii in np.arange(nSig):
                # hide the line(s) for spots marked not-visible (e.g. via
                # the 'v' key toggle), same convention as
                # SignalWidget.drawGraph()
                try:
                    isVisible = self.table['visible'][ii] == 'True'
                except (IndexError, KeyError, TypeError):
                    isVisible = True
                try:
                    self.penList[ii].setColor(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))
                except:
                    logger.exception('error occurred in drawSpectraGraph - could not set color')
                try:
                    # fit line
                    self.linePlotList2[ii].setData(w, fitSpectra[ii],
                                            pen = self.penList[ii])
                    self.linePlotList2[ii].show() if isVisible else self.linePlotList2[ii].hide()
                    # peak line
                    self.linePlotList3[ii].setData(fitPeak[ii][0],fitPeak[ii][1],
                                                   pen = self.penList[ii] )
                    self.linePlotList3[ii].show() if isVisible else self.linePlotList3[ii].hide()
                except:
                    logger.exception('error occurred in drawSpectraGraph - could not draw')

            self.spectraGraph.setUpdatesEnabled(True)

        # hide extra lines
        # linePlotList2 is already hidden in super().drawSpectraGraph()
        if self.showRawSpectra == False:
            for ii in np.arange(self.maxNLine - nSig):
                self.linePlotList3[ii+nSig].hide()
        else:
            for ii in np.arange(self.maxNLine):
                self.linePlotList3[ii].hide()


if __name__ == "__main__":
    pass















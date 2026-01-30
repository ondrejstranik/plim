'''
class for viewing spots's plasmon resonance
'''
from spectralCamera.gui.spectralViewer.xywViewer import XYWViewer
from plim.algorithm.spotSpectra import SpotSpectra
from plim.algorithm.spotIdentification import SpotIdentification

import napari
import time
import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QLabel, QSizePolicy
from qtpy.QtCore import Qt

from magicgui import magicgui
from enum import Enum
from typing import Annotated, Literal

import numpy as np
import traceback

class SpotSpectraViewer(XYWViewer):
    ''' class viewing spectra of plasmon spots'''

    DEFAULT = {'nameGUI':'SpotSpectraViewer'}

    def __init__(self, xywImage=None, wavelength= None, **kwargs):
        ''' initialise the class '''

        super().__init__(xywImage=xywImage, wavelength= wavelength, **kwargs)

        # calculated parameters
        self.spotSpectra = SpotSpectra(self.xywImage)

        #gui parameters
        self.maskLayer = None # layer of the mask with spots and bcg area
        self.showRawSpectra = True
        self.spectraParameterGui = None

        # spectra widget
        self.lineplotList2 = []

        # set gui
        SpotSpectraViewer._setWidget(self)

    def _setWidget(self):
        ''' prepare the qui '''

        # set napari
        # add mask layer
        # define a colormap with transparent 0 values
        colors = np.linspace(
            start=[0, 1, 0, 1],
            stop=[1, 0, 0, 1],
            num=3,
            endpoint=True
        )
        colors[0] = np.array([0., 1., 0., 0])
        transparentRedGreen_colormap = {
        'colors': colors,
        'name': 'red_and_green',
        'interpolation': 'linear'
        }
        self.maskLayer = self.viewer.add_image(self.spotSpectra.getMask(), name='spot_mask',
        colormap=transparentRedGreen_colormap, opacity = 0.5)

        # set pyqt
        @magicgui(auto_call= 'True')
        def spectraParameterGui(
            showRawSpectra: bool = self.showRawSpectra,
            circle: bool = self.spotSpectra.circle,
            pxAve: int = self.spotSpectra.pxAve,
            pxBcg: int = self.spotSpectra.pxBcg,
            pxSpace: int = self.spotSpectra.pxSpace,
            ratio: float = self.spotSpectra.ratio,
            angle: int = self.spotSpectra.angle,
            darkCount: float = self.spotSpectra.darkCount
            ):

            spectraParameterGui._auto_call = False

            self.spotSpectra.circle = circle
            spectraParameterGui.circle.value = circle
            self.spotSpectra.pxAve = pxAve
            spectraParameterGui.pxAve.value = pxAve
            self.spotSpectra.pxBcg = pxBcg
            spectraParameterGui.pxBcg.value = pxBcg
            self.spotSpectra.pxSpace = pxSpace
            spectraParameterGui.pxSpace.value = pxSpace
            self.spotSpectra.ratio = ratio
            spectraParameterGui.ratio.value = ratio
            self.spotSpectra.angle = angle
            spectraParameterGui.angle.value = angle
            self.spotSpectra.darkCount = darkCount
            spectraParameterGui.darkCount.value = darkCount
            self.showRawSpectra = showRawSpectra
            self.updateSpectra()
            spectraParameterGui._auto_call = True


        #automatic identification of spots
        @magicgui
        def spotIdentGui():
            # identify the spot
            sI = SpotIdentification(self.xywImage)
            myPosition = sI.getPosition()
            myRadius = sI.getRadius()
            print(f'detected radius: {myRadius}')

            # update the spectra parameter
            self.pointLayer.data = myPosition
            self.spectraParameterGui(pxAve=int(myRadius))

        # add widget setParameterGui
        self.spectraParameterGui = spectraParameterGui
        dw = self.viewer.window.add_dock_widget(self.spectraParameterGui, name ='view param', area='bottom')
        if self.dockWidgetParameter is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetParameter,dw)
        self.dockWidgetParameter = dw

        # add widget spotIdentGui
        self.spotIdentGui = spotIdentGui
        dw = self.viewer.window.add_dock_widget(self.spotIdentGui, name ='spot Ident', area='bottom')
        if self.dockWidgetParameter is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetParameter,dw)
        self.dockWidgetParameter = dw

        # adapt the spectra widget
        # pre allocate extra new lines for the graph
        for _ in range(self.maxNLine):
            self.lineplotList2.append(self.spectraGraph.plot())
            self.lineplotList2[-1].hide()
            self._speedUpLineDrawing(self.lineplotList2[-1])        

    def setImage(self, image):
        ''' set the image '''
        # update the spotSpectra image first
        self.spotSpectra.wxyImage = image
        super().setImage(image)


    def calculateSpectra(self):
        ''' calculate spectra at the given points'''

        self.spotSpectra.setSpot(self.pointLayer.data)

        self.pointSpectra = self.spotSpectra.getA()

    def updateSpectra(self):
        super().updateSpectra()

        # update the mask in napari
        self.maskLayer.data = self.spotSpectra.getMask()

    def drawSpectraGraph(self):
        ''' draw all new lines in the spectraGraph '''

        # if there is no pointSpectra then do not continue
        try:
            nSig = len(self.pointSpectra)
        except:
            return
    
        # define pen object
        mypen = QPen()
        mypen.setWidth(0)


        self.spectraGraph.setUpdatesEnabled(False)
        for ii in np.arange(nSig):
            try:
                mypen.setColor(QColor.fromRgbF(*list(
                    self.pointLayer.face_color[ii])))
            except:
                pass

            if self.showRawSpectra:
                try:
                    self.lineplotList[ii].setData(self.wavelength,
                                            self.spotSpectra.spectraRawSpot[ii])
                    self.lineplotList[ii].show()
                    self.lineplotList2[ii].setData(self.wavelength,
                                            self.spotSpectra.spectraRawBcg[ii])
                    self.lineplotList2[ii].show()
                except:
                    print('error occurred in drawSpectraGraph - pointSpectra')
            else:
                try:
                    self.lineplotList[ii].setData(self.wavelength,
                                            self.spotSpectra.spectraSpot[ii])
                    self.lineplotList[ii].show()
                except:
                    print('error occurred in drawSpectraGraph - pointSpectra')

        # hide extra lines
        for ii in np.arange(self.maxNLine - nSig):
            self.lineplotList[ii+nSig].hide()
        if self.showRawSpectra:
            for ii in np.arange(self.maxNLine - nSig):
                self.lineplotList2[ii+nSig].hide()
        else:
            for ii in np.arange(nSig):
                self.lineplotList2[ii].hide()
        
        self.spectraGraph.setUpdatesEnabled(True)

        # set Title
        if self.showRawSpectra:
            self.spectraGraph.setTitle(f'Spectra')
            self.spectraGraph.setLabel('left', 'Intensity', units='a.u.')        
        else:
            self.spectraGraph.setTitle(f'1 - Transmission')
            self.spectraGraph.setLabel('left', 'percentage', units='a.u.')

    def updateSpectraGraph(self):
        ''' obsolete -  use drawSpectraGraph'''
        self.drawSpectraGraph()

if __name__ == "__main__":
    pass















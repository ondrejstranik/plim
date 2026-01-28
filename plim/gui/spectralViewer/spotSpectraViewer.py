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
 
    def __init__(self, xywImage=None, wavelength= None, **kwargs):
        ''' initialise the class '''

        super().__init__(xywImage=xywImage, wavelength= wavelength, **kwargs)

        # calculated parameters
        self.spotSpectra = SpotSpectra(self.xywImage)

        #gui parameters
        self.maskLayer = None # layer of the mask with spots and bcg area
        self.showRawSpectra = True
        self.spectraParameterGui = None

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

        self.lineplotList = []                
        self.spectraGraph.clear()

        if self.showRawSpectra:
            try:
                for ii in np.arange(len(self.pointSpectra)):
                    mypen = QPen(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))
                    mypen.setWidth(0)
                    # raw spot
                    lineplot = self.spectraGraph.plot(pen= mypen)
                    # speeding up drawing
                    lineplot = self._speedUpLineDrawing(lineplot)
                    lineplot.setData(self.wavelength, self.spotSpectra.spectraRawSpot[ii])
                    self.lineplotList.append(lineplot)
                    # raw bcg
                    lineplot = self.spectraGraph.plot(pen= mypen)
                    # speeding up drawing
                    lineplot = self._speedUpLineDrawing(lineplot)                    
                    lineplot.setData(self.wavelength, self.spotSpectra.spectraRawBcg[ii])
                    self.lineplotList.append(lineplot)
            except:
                print('error occurred in drawSpectraGraph')
                traceback.print_exc()
        else:
            for ii in np.arange(len(self.pointSpectra)):
                mypen = QPen(QColor.fromRgbF(*list(
                    self.pointLayer.face_color[ii])))
                mypen.setWidth(0)
                lineplot = self.spectraGraph.plot(pen= mypen)
                lineplot.setData(self.wavelength, self.pointSpectra[ii])
                self.lineplotList.append(lineplot)
            # print('error occurred in drawSpectraGraph')            
        # set Title
        if self.showRawSpectra:
            self.spectraGraph.setTitle(f'Spectra')
            self.spectraGraph.setLabel('left', 'Intensity', units='a.u.')        
        else:
            self.spectraGraph.setTitle(f'1 - Transmission')
            self.spectraGraph.setLabel('left', 'percentage', units='a.u.')

    def updateSpectraGraph(self):
        ''' update the lines in the spectra graph '''

        self.spectraGraph.setUpdatesEnabled(False)

        mypen = QPen()
        mypen.setColor(QColor("White"))
        mypen.setWidth(0)        

        if self.showRawSpectra:
            try:
                indLen = np.min((len(self.spotSpectra.spectraRawSpot),len(self.spotSpectra.spectraRawBcg)))
                for ii in np.arange(indLen):
                    myline = self.lineplotList[2*ii]
                    mypen.setColor(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))

                    myline.setData(self.wavelength,self.spotSpectra.spectraRawSpot[ii], pen = mypen)
                    myline = self.lineplotList[2*ii+1]
                    myline.setData(self.wavelength,self.spotSpectra.spectraRawBcg[ii], pen = mypen)
            except:
                print('error occurred in updateSpectraGraph')
                print(f'indLen {indLen}')
                print(f'ii {ii}')
                print(f'len(self.spotSpectra.spectraRawSpot) {len(self.spotSpectra.spectraRawSpot)}')
                traceback.print_exc()
        else:
            try:
                self.pointSpectra = self.spotSpectra.getA()
                for ii in np.arange(len(self.pointSpectra)):
                    myline = self.lineplotList[ii]
                    mypen.setColor(QColor.fromRgbF(*list(
                        self.pointLayer.face_color[ii])))
                    
                    myline.setData(self.wavelength,self.pointSpectra[ii], pen = mypen)

            except:
                print('error occurred in updateSpectraGraph')
                traceback.print_exc()

        self.spectraGraph.setUpdatesEnabled(True)
        self.spectraGraph.repaint()



if __name__ == "__main__":
    pass















'''
class for viewing spots spectra
'''
from spectralCamera.gui.spectralViewer.sViewer import SViewer
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
from timeit import default_timer as timer

class SpotSpectraViewer(SViewer):
    ''' class for viewing spots spectra'''

    DEFAULT = {'nameGUI':'SpotSpectraViewer'}

    def __init__(self, image=None, wavelength= None, **kwargs):
        ''' initialise the class '''

        super().__init__(image=image, wavelength= wavelength, **kwargs)

        # calculated parameters
        # upgrade spotSpectra class
        _image = self.spotSpectra.image 
        _wavelength = self.spotSpectra.wavelength 
        self.spotSpectra = SpotSpectra(image= _image,wavelength=_wavelength)

        #napari widget
        self.maskLayer = None # layer of the mask with spots and bcg area

        # spectra parameter widget
        self.spectraParameterGui = None
        self.showRawSpectra = True

        # graph widget
        self.linePlotList2 = []

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
        @magicgui(auto_call= 'True', 
                  pxAve={'min':1},
                  pxBcg={'min':1},
                  ratio={'min':0.01})
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

            # recalculate mask
            self.spotSpectra.setMask()
            # recalculate spectra
            self.calculateSpectra()
            # redraw
            self.redraw(modified='point')

            spectraParameterGui._auto_call = True

        #automatic identification of spots
        @magicgui
        def spotIdentGui():
            # identify the spot
            sI = SpotIdentification(self.spotSpectra.image)
            myPosition = sI.getPosition()
            myRadius = sI.getRadius()
            print(f'detected radius: {myRadius}')


            # restrict to the spots, whose whole mask is in the image
            self.spotSpectra.pxAve = int(myRadius)
            self.spotSpectra.setSpot(myPosition)
            self.spotSpectra.setMask()
            myPosition = myPosition[~self.spotSpectra.outliers]

            # update the points and radius of spots, recalculate/ redraw  spectra and mask
            self.spotSpectra.setSpot(myPosition)
            # avoid setting this signal
            with self.pointLayer.events.data.blocker():
                self.pointLayer.data = myPosition
            # emit the signal in this case
            self.spectraParameterGui(pxAve=int(myRadius))



            # emit signal 
            # TODO: check if it is right
            self.sigUpdateData.emit()

        # add widget setParameterGui
        self.spectraParameterGui = spectraParameterGui
        dw = self.viewer.window.add_dock_widget(self.spectraParameterGui, name ='view param', area='bottom')
        if self.dockWidgetParameter is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetParameter,dw)
        self.dockWidgetParameter = dw
        # register the graph in menu
        if self.window_menu is not None:
            self.window_menu.addAction(dw.toggleViewAction())

        # add widget spotIdentGui
        self.spotIdentGui = spotIdentGui
        dw = self.viewer.window.add_dock_widget(self.spotIdentGui, name ='spot Ident', area='bottom')
        if self.dockWidgetParameter is not None:
            self.viewer.window._qt_window.tabifyDockWidget(self.dockWidgetParameter,dw)
        self.dockWidgetParameter = dw
        # register the graph in menu
        if self.window_menu is not None:
            self.window_menu.addAction(dw.toggleViewAction())

        # adapt the spectra widget
        # pre allocate extra new lines for the graph
        for _ in range(self.maxNLine):
            self.linePlotList2.append(self.spectraGraph.plot())
            self.linePlotList2[-1].hide()
            self._speedUpLineDrawing(self.linePlotList2[-1])        

    def drawSpectraGraph(self):
        ''' draw all new lines in the spectraGraph
        rewrite the function
        '''
        # if there is no pointSpectra then do not continue
        try:
            nSig = len(self.spotSpectra.getSpectra())
        except:
            return
    
        self.spectraGraph.setUpdatesEnabled(False)
        
        # loop over all points
        for ii in np.arange(nSig):
            try:
                self.penList[ii].setColor(QColor.fromRgbF(*list(
                    self.pointLayer.face_color[ii])))
            except:
                print('error occurred in drawSpectraGraph - could not set color')
                traceback.print_exc()

            # show spectra signal and background
            if self.showRawSpectra:
                try:
                    self.linePlotList[ii].setData(self.spotSpectra.wavelength,
                                            self.spotSpectra.spectraRawSpot[ii],
                                            pen = self.penList[ii])
                    self.linePlotList[ii].show()
                    self.linePlotList2[ii].setData(self.spotSpectra.wavelength,
                                            self.spotSpectra.spectraRawBcg[ii],
                                            pen = self.penList[ii])
                    self.linePlotList2[ii].show()
                except:
                    print('error occurred in drawSpectraGraph - pointSpectra')
                    traceback.print_exc()

            # show processed spectra
            else:
                try:
                    self.linePlotList[ii].setData(self.spotSpectra.wavelength,
                                            self.spotSpectra.spectraSpot[ii],
                                            pen = self.penList[ii])
                    self.linePlotList[ii].show()
                except:
                    print('error occurred in drawSpectraGraph - pointSpectra')

        # hide extra lines
        for ii in np.arange(self.maxNLine - nSig):
            self.linePlotList[ii+nSig].hide()
        if self.showRawSpectra:
            for ii in np.arange(self.maxNLine - nSig):
                self.linePlotList2[ii+nSig].hide()
        else:
            for ii in np.arange(self.maxNLine):
                self.linePlotList2[ii].hide()
        
        self.spectraGraph.setUpdatesEnabled(True)

        # set Title
        if self.showRawSpectra:
            self.spectraGraph.setTitle(f'Spectra')
            self.spectraGraph.setLabel('left', 'Intensity', units='a.u.')        
        else:
            self.spectraGraph.setTitle(f'1 - Transmission')
            self.spectraGraph.setLabel('left', 'percentage', units='a.u.')

    def redraw(self, modified='all'):
        ''' only redraw the images, spectra. It does not recalculate it
         it overwrite the function
           '''
        start = timer()
        if (modified=='image') or (modified=='all'):
            self.spectraLayer.data = self.spotSpectra.getImage()
            self.drawSpectraGraph()           
        if (modified=='point') or (modified=='all'):
            self.maskLayer.data = self.spotSpectra.maskImage            
            self.drawSpectraGraph()
        end = timer()
        print(f'viewer redraw evaluation time {end -start} s')

    

if __name__ == "__main__":
    pass















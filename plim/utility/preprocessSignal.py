''' class to preprocess kinetic data for fit'''

from plim.algorithm.spotData import SpotData
from plim.algorithm.fileData import FileData
from spectralCamera.algorithm.gridSuperPixel import GridSuperPixel
import pyqtgraph as pg

import napari
import numpy as np

import matplotlib.pyplot as plt


class PreprocessSignal():
    ''' preprocess the binding kinetics signal from spot.
    load necessary info, cut the range, get spots on a grid
    '''
    def __init__(self,folder,fileMainName):
        ''' initialise the class '''

        self.folder = folder
        self.fileMainName = fileMainName

        self.spotPosition = None
        self.image = None
        self.time = None
        self.signal = None
        self.signalGrid = None
        self.nColumn = None
        self.nRow = None

        PreprocessSignal._loadData(self)
        PreprocessSignal._getSpotGrid(self)

    def _loadData(self):
        ''' load the data '''

        # load data
        self.fileData = FileData()
        self.fileData.loadAllFile(folder=self.folder,fileMainName=self.fileMainName)

        # transfer data
        self.spotPosition = self.fileData.spotSpectra.spotPosition
        self.image = self.fileData.spotSpectra.image

        # set time0 to the beginning
        self.fileData.spotData.time0 = self.fileData.spotData.time[0]
        (self.signal, self.time) = self.fileData.spotData.getData()

    def _getSpotGrid(self):
        ''' identify the position of spots on a grid. top left corner is [0,0]'''

        # characterize the grid
        self.gridSP = GridSuperPixel()
        self.gridSP.setGridPosition(self.spotPosition)
        self.gridSP.getGridInfo()
        self.gridSP.getPixelIndex()

        # move the origin to the top left
        _x0 = np.min(self.gridSP.imIdx[:,0])
        _y0 = np.min(self.gridSP.imIdx[:,1])
        self.gridSP.shiftIdx00([_x0,_y0])

        self.nRow = np.max(self.gridSP.imIdx[:,0])+1
        self.nColumn = np.max(self.gridSP.imIdx[:,1])+1

    def _signalOnGrid(self):
        ''' set signal into a regular grid x- along channel '''
        self.signalGrid = np.zeros((self.signal.shape[0],self.nRow, self.nColumn))

        for ii in range(self.signal.shape[1]):
            self.signalGrid[:,self.gridSP.imIdx[ii,0],
                            self.gridSP.imIdx[ii,1]] = self.signal[:,ii]

    def alignData(self, timeRange=None):
        ''' reduce the date to time Range and offSet them to zero at the beginning'''
        # reduce time
        if timeRange is not None:
            _timeRange = np.all([self.time>timeRange[0],self.time<timeRange[1]],axis=0)
            self.time = self.time[_timeRange]
            self.signal = self.signal[_timeRange]
            offSetTime = timeRange[0]
        else:
            offSetTime = 0

        # off set the data
        self.fileData.spotData.setOffset(offSetTime)
        self.signal = self.signal - self.fileData.spotData.getOffset()

        self._signalOnGrid()


    def showGrid(self, step=1):
        ''' show the indexing of the spots, grid showed in steps = step'''

        # prepare a sub selected  points
        pointsSelect = ((self.gridSP.imIdx[:,0]%step == 0 ) & 
                        (self.gridSP.imIdx[:,1]%step == 0 ) & 
                        self.gridSP.inside)
        
        points = self.gridSP.position[pointsSelect,:]

        features = {'pointIndex0': self.gridSP.imIdx[pointsSelect,0],
                    'pointIndex1': self.gridSP.imIdx[pointsSelect,1]
                    }
        text = {'string': '[{pointIndex0},{pointIndex1}]',
                'translation': np.array([-5, 0])
                }

        # display the images
        viewer = napari.Viewer()
        viewer.add_image(self.image)
        viewer.add_points(points,features=features,text=text, size= 5, opacity=0.5)

    def showSignal(self, axis=0, idx=None):
        ''' show selected line, coloring along axis, 
        idx .. index of row(axis=0) or column(axis=1) , None = all '''

        # add graph - line along y
        graph = pg.plot()
        if axis==0: graph.setTitle(f'Signals - (rows - same color)')
        else: graph.setTitle(f'Signals - (column - same color)')
        
        graph.setLabel('left', 'Signal', units='nm')
        graph.setLabel('bottom', 'time', units= 's')


        if axis==0:
            idxC = range(self.nColumn)
            idxR = range(self.nRow) if idx is None else idx 
        else:
            idxR = range(self.nRow)
            idxC = range(self.nColumn) if idx is None else idx 

        for jj in idxR:
            for ii in idxC:
                if axis==0:
                    graph.plot(self.time,self.signalGrid[:,jj,ii], pen=(jj,self.nRow))
                else:
                    graph.plot(self.time,self.signalGrid[:,jj,ii], pen=(ii,self.nColumn))


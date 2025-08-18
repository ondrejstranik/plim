''' script to analyse the signals from plasmon spots'''
#%%
# import and parameter definition

import numpy as np
import napari

from qtpy.QtWidgets import (
    QApplication,QMainWindow,QWidget,QToolBar,QVBoxLayout, QFileDialog, QLabel)
import pyqtgraph.exporters
import csv

import sys
from pathlib import Path

from plim.algorithm.spotData import SpotData
from plim.algorithm.flowData import FlowData
from plim.algorithm.fileData import FileData

from plim.gui.signalViewer.signalWidget import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
from plim.gui.signalViewer.infoWidget import InfoWidget
from plim.gui.signalViewer.fitWidget import FitWidget


class Window(QMainWindow):
    '''  main class for data analysis
    '''

    DEFAULT = { 'fileMainName' : 'Experiment1',
                'folder' : r'g:\office\work\projects - funded\21-10-01 LPI\LPI\24-08-28 spr_variable_array\iso_h20_1to4',
                'loadDefault': False }


    def __init__(self,**kwarg):
        super().__init__(parent=None)

        # file parameters
        self.fileMainName = self.DEFAULT['fileMainName']
        self.folder = self.DEFAULT['folder']
    
        # data parameters
        self.spotPosition = None
        self.image = None
        self.w = None
        self.flow = None
        self.time = None
        #self.signal = None
        self.sD: SpotData = None
        self.fD: FlowData = None
        #self.fileData = FileData()

        # widget / widgets parameters
        self.infoLabel = None
        self.viewer = None
        self.spotLayer = None
        self.imageLayer = None
        self.sW = None
        self.fW = None
        self.iW = None

        self._createToolBar()

        if self.DEFAULT['loadDefault']:
            self._loadData()
        else:
            fileMainName = None
            while fileMainName is None:
                folder, fileMainName = self._selectFile()
            self.folder = folder
            self.fileMainName = fileMainName        
            self._loadData()

        self._createWidget()


    def _createToolBar(self):
        tools = QToolBar()
        tools.addAction("Load", self.LoadPressed)
        tools.addAction("Save", self.SavePressed)
        tools.addAction("Export", self.ExportPressed)
        tools.addAction("Exit", self.closeAll)
        self.addToolBar(tools)

    def _selectFile(self):
        ''' select file with the gui window
        return path -- string and fileMainName --string
        '''
        dialog = QFileDialog(self)
        dialog.setDirectory(__file__)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Numpy arrays (*.npz)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        filenames = []
        if dialog.exec():
            filenames = dialog.selectedFiles()
        
        if filenames:
            p = Path(filenames[0])
            _name = p.stem
            fileMainName = '_'.join(_name.split('_')[:-1])
            return str(p.parent) , fileMainName
        else:
            return None , None
    
    def ExportPressed(self):
        dialog = QFileDialog(self)
        dialog.setDirectory(__file__)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        folder = None
        if dialog.exec():
            folder = dialog.selectedFiles()
        
        if folder is not None:
            # save napari overview image
            self.viewer.theme = "light"
            export_figure = self.viewer.screenshot(path=folder[0] +r"/image.png")
            self.viewer.theme = "dark"
            print('viewer image exported')

            # save signal graph
            exporter = pyqtgraph.exporters.ImageExporter(self.sW.graph.plotItem)
            # set export parameters if needed
            #exporter.parameters()['width'] = 100   # (note this also affects height parameter)
            exporter.export(folder[0] +r"/signal.png")
            print('signal graph exported')

            # save flow graph
            exporter = pyqtgraph.exporters.ImageExporter(self.fW.graph.plotItem)
            # set export parameters if needed
            #exporter.parameters()['width'] = 100   # (note this also affects height parameter)
            exporter.export(folder[0] +r"/flow.png")
            print('flow graph exported')

            # save info table
            _dict = {'dSignal': self.sD.dSignal, 'noise': self.sD.noise}
            _dataDict = self.sD.table | _dict
            
            with open(folder[0] +r"/infoTable.txt", "w") as outfile:
            
                # pass the csv file to csv.writer function.
                #writer = csv.writer(outfile, delimiter ='\t')
                writer = csv.writer(outfile, delimiter =',')


                # pass the dictionary keys to writerow
                # function to frame the columns of the csv file
                writer.writerow(_dataDict.keys())
            
                # make use of writerows function to append
                # the remaining values to the corresponding
                # columns using zip function.
                writer.writerows(zip(*_dataDict.values()))
            print('info data exported')

    def SavePressed(self):
        self._saveData()

    def LoadPressed(self):

        folder, fileMainName = self._selectFile()
        if fileMainName is not None:
            self.folder = folder
            self.fileMainName = fileMainName        
            self._loadData()
            self._updateInfoLabel()

        # update data widgets
        self.sW.sD = self.sD
        self.iW.sD = self.sD
        self.imageLayer.data = self.image
        # update widgets
        self.sW.lineParameter(
                lineIndex = self.sW.lineIndex,
                lineName = self.sW.sD.table['name'][self.sW.lineIndex],
                lineVisible = self.sW.sD.table['visible'][self.sW.lineIndex]=='True',
                lineColor = self.sW.sD.table['color'][self.sW.lineIndex],
                evalTime = self.sW.sD.evalTime,
                dTime = self.sW.sD.dTime
        )
        self.sW.drawGraph()
        self.fW.drawGraph()

    def _updateInfoLabel(self):
        ''' update info label '''
        self.infoLabel.setText(self.folder + '\n' + self.fileMainName)

    def _saveData(self, folder= None, fileMainName=None):
        ''' save info Data '''
        if folder is not None: self.folder = folder
        if fileMainName is not None: self.fileMainName = fileMainName

        # set the data into the saving data class fileData
        _fileData = FileData(spotData=self.sD)
        _fileData.saveInfoFile(self.folder,self.fileMainName)
        print('saving info file')


    def _loadData(self,folder= None, fileMainName=None):
        ''' load all possible data from files '''

        if folder is None: folder = self.folder 
        if fileMainName is None: fileMainName = self.fileMainName

        _fileData = FileData()
        _fileData.loadAllFile(folder=folder,fileMainName=fileMainName)

        # image data
        self.spotPosition = _fileData.spotSpectra.spotPosition
        self.image = _fileData.spotSpectra.wxyImage
        self.w = _fileData.pF.wavelength

        # spot Data 
        # done in this way, so that that all parameters in sD are properly updated
        #self.sD = SpotData()

        # copy info data parameters as well
        self.sD = _fileData.spotData

        #self.sD.setData(signal=_fileData.spotData.signal,time=_fileData.spotData.time,
        #                table=_fileData.spotData.table)
        self.sD.time0 = self.sD.time[0]

        # flow data
        if self.fD is None:
            self.fD = FlowData()

        try:
            self.fD.setData(signal=_fileData.flowData.signal, time=_fileData.flowData.time)
            # synchronise the origin of the time0 with flow data if provided
            self.sD.time0 = self.fD.time0
        except:
            print('error loading flow data')

        # update spotData
        self.sD.setOffset()
        self.sD.getDSignal()
        self.sD.getNoise()
        self.sD.setTable(table=self.sD.table)


    def closeAll(self):
        self.sW.close()
        self.iW.close()
        self.fW.close()
        self.viewer.close()
        self.close()

    def redrawViewer(self):
        ''' update napari Viewer'''

        # updating spots position
        try:
            if np.any(self.spotLayer.data -self.spotPosition):
                self.spotLayer.data = self.spotPosition
        except:
            self.spotLayer.data = self.spotPosition


        # updating spot features
        self.spotLayer.features = {
            'names': self.sD.table['name']
        }
        rgb = self.sD.table['color']
        vis = self.sD.table['visible']
        _color = [rgb[ii] + 'ff' if vis[ii]=='True' else rgb[ii] + '00' for ii in range(len(rgb))]

        self.spotLayer.face_color = _color


    def updateColorFromNapari(self):
        ''' update color from Napari, update spot and info widget'''
 
        print(f'updating from Napari - color')
    
        # update color in spotData
        _fc = 1*self.spotLayer.face_color #  deep copy of the colors
        _fc[list(self.spotLayer.selected_data)] = self.spotLayer._face.current_color # adjust the just modified 
        _fcHex = ['#{:02x}{:02x}{:02x}'.format( *ii.tolist()) for ii in (_fc*255).astype(int)]
        self.sD.table['color'] = _fcHex

        #TODO: this do not really update the color immediately. Try to figure out something else
        # update the color selection according the visibility
        rgb = self.sD.table['color']
        vis = self.sD.table['visible']
        _color = [rgb[ii] + 'ff' if vis[ii]=='True' else rgb[ii] + '00' for ii in list(self.spotLayer.selected_data)]
        print(f'current_color {_color}')
        self.spotLayer._face.current_color = _color

        self.iW.redrawWidget()
        self.sW.redrawWidget()

    def updateSelectionFromNapari(self):

        print(f'updating from Napari - selection')
        # selected layers
        spotList = list(self.spotLayer.selected_data)
        if spotList:
            self.sW.lineIndex = spotList[0]
            self.sW.redrawWidget()
            self.iW.updateSelect(spotList)

    def updateVisibilityFromNapari(self):

        print(f'updating from Napari - visibility')
        # selected layers
        _idx = list(self.spotLayer.selected_data)
        if _idx == []:
            return 
        if self.sD.table['visible'][_idx[0]]=='True':
            for ii in _idx:
                self.sD.table['visible'][ii] = 'False'
        else:
            for ii in _idx:
                self.sD.table['visible'][ii] = 'True'

        self.redrawViewer()
        self.iW.redrawWidget()
        self.sW.redrawWidget()

    def updateFromSW(self):
        ''' update napari and info widget '''

        print(f'updating from sW')
        self.iW.redrawWidget()
        self.iW.updateSelect(self.sW.lineIndex)
        self.redrawViewer()

    def updateFromIW(self,**kwargs):
        ''' update napari and signal widget'''

        print('updatingFrom IW')
        self.sW.redrawWidget()
        self.redrawViewer()

    def addDeltaSignalLayer(self):
        ''' add delta signal layer into napari '''
        _image = np.zeros(self.image.shape[1:])
        spotR = int(np.mean(self.spotLayer.size[0])/2)

        for ii,_spotPosition in enumerate(self.spotPosition):
            if self.sD.table['visible'][ii]=='True':
                _y = int(_spotPosition[0])
                _x = int(_spotPosition[1])
                _image[_y-spotR+1:_y+spotR+1,
                      _x-spotR+1:_x+spotR+1] = self.sD.dSignal[ii]

        _name = f'delta Signal @ {self.sD.evalTime+self.sD.dTime} s '
        self.signalLayer = self.viewer.add_image(_image, name= _name)

    def addColorBar(self):
        ''' create image of a color bar in new viewer '''

        try:
            _layer = self.viewer.layers.selection.active
            barViewer = napari.Viewer()
            
            im = _layer.data
            gamma = _layer.gamma
            LMax = _layer.contrast_limits[1]
            LMin = _layer.contrast_limits[0]
            yMin = np.max((_layer.contrast_limits[0],im.min()))
            yMax =  np.min((_layer.contrast_limits[1],im.max()))

            yRange = np.linspace(yMin,yMax)
            xRange = ((yRange - LMin)/(LMax - LMin))**(1/gamma)
            
            length = 50
            cb = _layer.colormap.map(xRange)
            cb = cb[::-1,None,...]
            barViewer.add_image(cb, name= 'colorbar ' + _layer.name)
            points = np.array([[length,0],[0,0]])
            features = {'value': np.array([yMin, yMax])}
            text = {
                'string': '{value:.2f}',
                'size': 20,
                'color': 'white',
                'translation': np.array([0,5]),
            }
            points_layer = barViewer.add_points(
                points, features=features,text=text,size=0)
        except:
            print('can not create colorbar')

    def _createWidget(self):

        # info text 
        self.infoLabel = QLabel('', self) 
        self._updateInfoLabel()
        self.setCentralWidget(self.infoLabel)

        # napari viewer
        self.viewer = napari.Viewer()
        self.imageLayer = self.viewer.add_image(self.image)
        self.spotLayer = self.viewer.add_points(np.array([[0,0]]))
        self.spotLayer.features = {'names': ['0']}
        self.spotLayer.text = {
                'string': '{names}',
                'size': 20,
                'color': 'green',
                'translation': np.array([-5, 0])}
        self.spotLayer._face.events.current_color.connect(self.updateColorFromNapari)
        self.viewer.bind_key('s',lambda x: self.updateSelectionFromNapari())
        self.viewer.bind_key('v',lambda x: self.updateVisibilityFromNapari())
        self.viewer.bind_key('d',lambda x: self.addDeltaSignalLayer())
        self.viewer.bind_key('b',lambda x: self.addColorBar())


        # signal widget
        self.sW = SignalWidget(spotData=self.sD)
        #self.sW.sD = self.sD
        self.sW.show()
        self.sW.sigUpdateData.connect(self.updateFromSW)

        # flow rate widget
        self.fW = FlowRateWidget(flowData=self.fD)
        self.fW.show()
        self.sW.graph.setXLink(self.fW.graph) # connect time axis 

        # info widget
        self.iW = InfoWidget(self.sD)
        self.iW.show()
        self.iW.sigUpdateData.connect(self.updateFromIW)
        
        # fit widget
        self.fW = FitWidget()
        self.fW.show()
        self.fW.connectSignalWidget(self.sW)

        # initial update
        self.updateFromSW()


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())




#%%
''' class to process videos of hyperspectral images'''
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

from plim.gui.signalViewer.signalWidget import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
from plim.gui.signalViewer.infoWidget import InfoWidget


class Window(QMainWindow):
    '''  main class for data analysis
    '''

    DEFAULT = {'nameSet'  : {
                            'flow':'_flowData.npz',
                            'image': '_image.npz',
                            'spot': '_spotData.npz',
                            'fit': '_fit.npz',
                            'info': '_info.dat'
                            },
                'fileMainName' : 'Experiment1',
                'folder' : r'g:\office\work\projects - funded\21-10-01 LPI\LPI\24-08-28 spr_variable_array\iso_h20_1to4',
                'loadDefault': True }


    def __init__(self,**kwarg):
        super().__init__(parent=None)

        # file parameters
        self.fileMainName = self.DEFAULT['fileMainName']
        self.folder = self.DEFAULT['folder']
    
        # data parameters

        # widget / widgets parameters
        self.pW = None

        self._createToolBar()

        if self.DEFAULT['loadDefault']:
            self._loadData()

        self._createWidget()


    def _createToolBar(self):
        tools = QToolBar()
        tools.addAction("Load", self.LoadPressed)
        tools.addAction("Save", self.SavePressed)
        tools.addAction("Exit", self.closeAll)
        self.addToolBar(tools)

    def _selectFile(self):
        ''' select file with the gui window
        return path -- string and fileMainName --string
        '''
        dialog = QFileDialog(self)
        dialog.setDirectory(__file__)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("Numpy arrays (*.npy)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        if dialog.exec():
            filenames = dialog.selectedFiles()
        
        if filenames:
            p = Path(filenames[0])
            _name = p.stem
            fileMainName = '_'.join(_name.split('_')[:-1])
            return str(p.parent) , fileMainName
        else:
            return None
    

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
        self.sW.lineParameter()
        self.sW.drawGraph()

    def _updateInfoLabel(self):
        ''' update info label '''
        self.infoLabel.setText(self.folder + '\n' + self.fileMainName)

    def _saveData(self, folder= None, fileMainName=None):

        if folder is not None: self.folder = folder
        if fileMainName is not None: self.fileMainName = fileMainName

        self.sD.saveInfo(fullfile= str(self.folder + 
                                       '/' + self.fileMainName 
                                       + self.DEFAULT['nameSet']['info']))
        print('saving info file')


    def _loadData(self,folder= None, fileMainName=None):
        ''' load all possible data from files '''

        if folder is None: folder = self.folder 
        if fileMainName is None: fileMainName = self.fileMainName
        
        nameSet = self.DEFAULT['nameSet']

        # load image
        container1 = np.load(folder + '/' + fileMainName + nameSet['image'])
        self.spotPosition = container1['arr_0']
        self.image = container1['arr_1']
        self.w = container1['arr_2']

        # load flow
        container2 = np.load(folder + '/' + fileMainName + nameSet['flow'])
        self.flow = container2['arr_0']
        self.time = container2['arr_1']

        # load spot
        container3 = np.load(folder + '/' + fileMainName + nameSet['spot'])
        self.signal = container3['arr_0']

        # set default spot info
        self.sD = SpotData(self.signal, self.time)

        try:
            self.sD.loadInfo(folder + '/' + fileMainName + nameSet['info'])
        except:
            print('no file info')


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

        # signal widget
        self.sW = SignalWidget(spotData=self.sD)
        #self.sW.sD = self.sD
        self.sW.show()
        self.sW.sigUpdateData.connect(self.updateFromSW)

        # flow rate widget
        self.fW = FlowRateWidget(signal=self.flow, time = self.time)
        self.fW.show()

        # info widget
        self.iW = InfoWidget(self.sD)
        self.iW.show()
        self.iW.sigUpdateData.connect(self.updateFromIW)
        
        # initial update
        self.updateFromSW()


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
    #napari.run()



#%%
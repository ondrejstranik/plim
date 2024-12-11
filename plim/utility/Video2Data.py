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
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer


class Window(QMainWindow):
    '''  main class for data analysis
    '''

    DEFAULT = {'nameSet'  : {
                            'flow':'_flowData.npz',
                            'image': '_image.npz',
                            'spot': '_spotData.npz',
                            'fit': '_fit.npz',
                            'info': '_info.dat',
                            'wavelength': 'wavelength.npy'
                            },
                'fileMainName' : 'time_1726482816858315000.npy',
                'folder' : r'D:\LPI\24-9-16 pfcamera\video',
                'loadDefault': True }


    def __init__(self,**kwarg):
        super().__init__(parent=None)

        # file parameters
        self.fileMainName = self.DEFAULT['fileMainName']
        self.folder = self.DEFAULT['folder']
    
        # data parameters
        self.image = None
        self.w = None

        # widget / widgets parameters
        self.pV = None
        self.infoLabel = None

        self._createToolBar()

        if self.DEFAULT['loadDefault']:
            self._loadData()

        self._createWidget()


    def _createToolBar(self):
        tools = QToolBar()
        tools.addAction("Load Image", self.LoadImagePressed)
        tools.addAction("Load Point", self.LoadPointPressed)
        tools.addAction("Save Point", self.SavePointPressed)
        tools.addAction("Export Signal", self.ExportSignalPressed)
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
            fileMainName = p.name 
            return str(p.parent) , fileMainName
        else:
            return None
    

    def SavePointPressed(self):
        self._saveData()

    def LoadPointPressed(self):
        pass

    def ExportSignalPressed(self):
        pass

    def LoadImagePressed(self):

        folder, fileMainName = self._selectFile()
        if fileMainName is not None:
            self.folder = folder
            self.fileMainName = fileMainName        
            self._loadData()
            self._updateInfoLabel()
            self.pV.setImage(self.image)
            self.pV.setWavelength(self.w)

    def _updateInfoLabel(self):
        ''' update info label '''
        self.infoLabel.setText(self.folder + '\n' + self.fileMainName)

    def _saveData(self, folder= None, fileMainName=None):

        if folder is not None: self.folder = folder
        if fileMainName is not None: self.fileMainName = fileMainName

        #self.sD.saveInfo(fullfile= str(self.folder + 
        #                               '/' + self.fileMainName 
        #                               + self.DEFAULT['nameSet']['info']))
        #print('saving info file')


    def _loadData(self,folder= None, fileMainName=None):
        ''' load all possible data from files '''

        if folder is None: folder = self.folder 
        if fileMainName is None: fileMainName = self.fileMainName
        
        nameSet = self.DEFAULT['nameSet']
        
        # load image
        self.image = np.load(self.folder + '/' + fileMainName)
        self.w = np.load(self.folder + '/' + nameSet['wavelength'])

        #self._updateInfoLabel()
        #self.pV.setImage(self.image)
        #self.pV.setWavelength(self.w)



    def closeAll(self):
        self.pV.viewer.close()
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
        self.pV = PlasmonViewer(self.image,self.w)


if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
    #napari.run()



#%%
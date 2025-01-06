''' 
script to run  gui for processing video of hyper-spectral images
'''
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
import re

from spectralCamera.algorithm.fileSIVideo import FileSIVideo

from plim.algorithm.spotData import SpotData
from plim.algorithm.spotSpectra import SpotSpectra
from plim.algorithm.fileData import FileData

from plim.gui.signalViewer.signalWidget import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
from plim.gui.signalViewer.infoWidget import InfoWidget
from plim.gui.spectralViewer.plasmonViewer import PlasmonViewer


class Window(QMainWindow):
    '''  gui class for data analysis of the videos of spectral images
    '''

    DEFAULT = { 'fileMainName' : 'time_1726482816858315000.npy',
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
            _fileSIVideo = FileSIVideo(folder=self.folder)
            self.w = _fileSIVideo.loadWavelength()
            self.image = _fileSIVideo.loadImage(self.fileMainName)

        self._createWidget()


    def _createToolBar(self):
        tools = QToolBar()
        tools.addAction("Load Image", self.LoadImagePressed)
        tools.addAction("Load Info", self.LoadInfoPressed)
        tools.addAction("Export Signal", self.ExportSignalPressed)
        tools.addAction("Exit", self.closeAll)
        self.addToolBar(tools)

    def _selectFile(self,nameFilter= "all (*.*)"):
        ''' select file with the gui window
        return path -- string and fileMainName --string
        '''
        dialog = QFileDialog(self)
        dialog.setDirectory(__file__)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter(nameFilter)
        dialog.setViewMode(QFileDialog.ViewMode.List)
        filenames = None
        if dialog.exec():
            filenames = dialog.selectedFiles()
        
        if filenames:
            p = Path(filenames[0])
            fileMainName = p.name 
            return str(p.parent) , fileMainName
        else:
            return None
    
    def LoadInfoPressed(self):
        ''' loading the fitting parameters / spot positions'''

        folder, _fileMainName = self._selectFile(nameFilter="Zipped numpy arrays (*.npz)")

        if _fileMainName is not None:
            fileType = '_'+_fileMainName.split('_')[-1]
            fileMainName = '_'.join(_fileMainName.split('_')[:-1])
            print(f'fileType = {fileType}')

            _fileData = FileData()

            # load fit parameter from file
            if fileType == _fileData.DEFAULT['nameSet']['fit']:
                _fileData.loadFitFile(folder=folder, fileMainName= fileMainName)
                self.pV.fitParameterGui(
                    wavelengthStart= _fileData.pF.wavelengthStartFit,
                    wavelengthStop = _fileData.pF.wavelengthStopFit,
                    orderFit = _fileData.pF.orderFit,
                    peakWidth = _fileData.pF.peakWidth,
                    wavelengthGuess = _fileData.pF.wavelengthGuess)

                self.pV.spectraParameterGui(
                    circle= _fileData.spotSpectra.circle,
                    pxAve= _fileData.spotSpectra.pxAve,
                    pxBcg= _fileData.spotSpectra.pxBcg,
                    pxSpace= _fileData.spotSpectra.pxSpace,
                    ratio= _fileData.spotSpectra.ratio,
                    angle= _fileData.spotSpectra.angle,
                    darkCount= _fileData.spotSpectra.darkCount
                )

            # load spot position from file
            if fileType == _fileData.DEFAULT['nameSet']['image']:
                _fileData.loadImageFile(folder=folder, fileMainName= fileMainName)                
                self.pV.pointLayer.data = _fileData.spotSpectra.spotPosition
                print(f'spot position {_fileData.spotSpectra.spotPosition}')
                self.pV.updateSpectra()

    def ExportSignalPressed(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        (fileName, _ )  = QFileDialog.getSaveFileName(self, 
            "Export File Name", "", "All Files(*)", options = options)
        
        if fileName:
            p=Path(fileName)
            folder = str(p.parent)
            fileMainName = str(p.stem)

            _fileData = FileData(spotSpectra=self.pV.spotSpectra,
                                 plasmonFit= self.pV.pF)
            _fileData.spotSpectra.setImage(self.pV.spotSpectra.wxyImage)

            _fileData.saveImageFile(folder=folder,fileMainName=fileMainName)
            _fileData.saveFitFile(folder=folder,fileMainName=fileMainName)

            _spotData = self._generateSpotSignal()
            _fileData.spotData = _spotData
            _fileData.saveSpotFile(folder=folder,fileMainName=fileMainName)

    def _generateSpotSignal(self):
        ''' generate signal from the raw images'''
        import copy 

        print('starting loading/fitting raw files')
        _sS = copy.deepcopy(self.pV.spotSpectra)
        _pF = copy.deepcopy(self.pV.pF)

        _fileSIVideo = FileSIVideo(self.folder)
        
        fileName, fileTime =_fileSIVideo.getImageInfo()
        nFiles = len(fileName)
        
        _time = fileTime/1e9 # convert to seconds
        _signal = np.zeros((nFiles,_sS.spotPosition.shape[0])) # define matrix

        # process the images
        for ii,_fileImage in enumerate(fileName):
            print(f'{ii} out of {nFiles}')
            _image = _fileSIVideo.loadImage(_fileImage)
            _sS.setImage(_image)
            _sS.calculateSpectra()
            _spectra = np.array(_sS.getA())
            _pF.setSpectra(_spectra)
            _pF.calculateFit()
            _signal[ii,:] = _pF.getPosition()
        
        print(f'signal = {_signal}')
        print(f'time [s]= {_time}')

        _spotData = SpotData(signal=_signal,time=_time)
        return _spotData

    def LoadImagePressed(self):

        folder, fileMainName = self._selectFile(nameFilter="Numpy arrays (*.npy)")
        if fileMainName is not None:
            self.folder = folder
            self.fileMainName = fileMainName        
            _fileSIVideo = FileSIVideo(folder=self.folder)
            self.w = _fileSIVideo.loadWavelength()
            self.image = _fileSIVideo.loadImage(self.fileMainName)
            self._updateInfoLabel()
            self.pV.setImage(self.image)
            self.pV.setWavelength(self.w)

    def _updateInfoLabel(self):
        ''' update info label '''
        self.infoLabel.setText(self.folder + '\n' + self.fileMainName)

    def closeAll(self):
        self.pV.viewer.close()
        self.close()

    def _createWidget(self):

        # info text 
        self.infoLabel = QLabel('', self) 
        self._updateInfoLabel()
        self.setCentralWidget(self.infoLabel)

        # plasmon viewer
        self.pV = PlasmonViewer(self.image,self.w)



if __name__ == "__main__":
    app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
    #napari.run()



#%%
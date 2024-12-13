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

        folder, fileMainName = self._selectFile(nameFilter="Zipped numpy arrays (*.npz)")

        if fileMainName is not None:
            fileType = '_'+fileMainName.split('_')[-1]  
            print(f'fileType = {fileType}')

            # load fit parameter from file
            if fileType == self.DEFAULT['nameSet']['fit']:
                container = np.load(folder + '/' + fileMainName)
                # update values if present in the file                
                if 'wavelengthStartFit' in container: self.pV.fitParameterGui.wavelengthStart.value =container['wavelengthStartFit']
                if 'wavelengthStopFit' in container: self.pV.fitParameterGui.wavelengthStop.value= container['wavelengthStopFit']
                if 'orderFit' in container: self.pV.fitParameterGui.orderFit.value= container['orderFit']
                if 'peakWidth' in container: self.pV.fitParameterGui.peakWidth.value = container ['peakWidth']
                if 'wavelengthGuess' in container: self.pV.fitParameterGui.wavelengthGuess.value = container['wavelengthGuess']
                self.pV.fitParameterGui()

                if 'pxBcg' in container: self.pV.spectraParameterGui.pxBcg.value = container['pxBcg']
                if 'pxAve' in container: self.pV.spectraParameterGui.pxAve.value = container['pxAve']
                if 'pxSpace' in container: self.pV.spectraParameterGui.pxSpace.value = container['pxSpace']
                if 'darkCount' in container: self.pV.spectraParameterGui.darkCount.value = container['darkCount']
                if 'ratio' in container: self.pV.spectraParameterGui.ratio.value = container['value']
                if 'angle' in container: self.pV.spectraParameterGui.angle.value = container['angle'] 
                self.pV.spectraParameterGui()

            # load spot position from file
            if fileType == self.DEFAULT['nameSet']['image']:
                container = np.load(folder + '/' + fileMainName)
                self.pV.pointLayer.data = container['arr_0']
                self.pV.updateSpectra()
                print(f"loading spot position {container['arr_0']}")


    def ExportSignalPressed(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, 
            "Export File Name", "", "All Files(*)", options = options)
        
        if fileName:
            p=Path(fileName)
            folder = str(p.parent)
            fileMainName = str(p.stem)

            np.savez(folder +'/' + fileMainName + self.DEFAULT['image'],
            spotPosition = self.pV.spotSpectra.spotPosition,
            image = self.pV.spotSpectra.wxyImage,
            wavelength = self.pV.wavelength)
            
            np.savez(folder +'/' + fileMainName + self.DEFAULT['fit'],
            pxBcg = self.pV.spotSpectra.pxBcg,
            pxAve = self.pV.spotSpectra.pxAve,
            pxSpace = self.pV.spotSpectra.pxSpace,
            darkCount = self.pV.spotSpectra.darkCount,
            wavelengthStartFit = self.pV.pF.wavelengthStartFit,
            wavelengthStopFit = self.pV.pF.wavelengthStopFit,
            orderFit = self.pV.pF.orderFit,
            wavelengthGuess = self.pV.pF.wavelengthGuess,
            peakWidth = self.pV.pF.peakWidth                        
            )





    def _generateSpotSignal(self):
        ''' generate signal from the raw images'''







    def LoadImagePressed(self):

        folder, fileMainName = self._selectFile(nameFilter="Numpy arrays (*.npy)")
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

        #TODO: save the data

        #self.sD.saveInfo(fullfile= str(self.folder + 
        #                               '/' + self.fileMainName 
        #                               + self.DEFAULT['nameSet']['info']))
        #print('saving info file')


    def _loadData(self,folder= None, fileMainName=None):
        ''' load image data from files '''

        if folder is None: folder = self.folder 
        if fileMainName is None: fileMainName = self.fileMainName
        
        nameSet = self.DEFAULT['nameSet']
        
        # load image
        self.image = np.load(self.folder + '/' + fileMainName)
        self.w = np.load(self.folder + '/' + nameSet['wavelength'])




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
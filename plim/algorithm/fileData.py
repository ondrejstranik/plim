"""
FileData - class for unified saving/loading data generated in plim experiment

Created on Mon Nov 15 12:08:51 2021

@author: ostranik
"""
#%%

#TODO: correct time loading !!!!!!!!!!!!
import os
import time
import numpy as np
import pickle
from pathlib import Path


from plim.algorithm.plasmonFit import PlasmonFit
from plim.algorithm.spotSpectra import SpotSpectra
from plim.algorithm.spotData import SpotData
from plim.algorithm.flowData import FlowData


class FileData:
    ''' class to save load all relevant data  '''
    
    DEFAULT = {'nameSet'  : {
                            'flow':'_flowData.npz',
                            'image': '_image.npz',
                            'spot': '_spotData.npz',
                            'fit': '_fit.npz',
                            'info': '_info.dat'
                            }
                            }

    def __init__(self,spotData=None,spotSpectra=None, plasmonFit=None, flowData=None, **kwargs):
        ''' initialisation '''

        # data container
        self.pF = PlasmonFit() if spotData is None else plasmonFit
        self.spotSpectra = SpotSpectra() if spotSpectra is None else spotSpectra
        self.spotData = SpotData() if spotData is None else spotData
        self.flowData = FlowData() if flowData is None else flowData

    def saveImageFile(self,folder,fileMainName):
        ''' save image file'''
        np.savez(str(folder) + '/' +  str(fileMainName) + self.DEFAULT['nameSet']['image'],
        spotPosition = self.spotSpectra.spotPosition,
        image = self.spotSpectra.wxyImage,
        wavelength = self.pF.wavelength)

    def loadImageFile(self,folder,fileMainName):
        ''' loading image file'''

        _file = Path(folder + '/' + fileMainName + self.DEFAULT['nameSet']['image'])        
        if not _file.is_file():
            print(f'could not find file {_file}')
            return

        container1 = np.load(_file)
        if 'spotPosition' in container1.keys():
            self.spotSpectra.spotPosition = container1['spotPosition']
        if 'arr_0' in container1.keys():
            self.spotSpectra.spotPosition = container1['arr_0'] # back compatibility
        if 'image' in container1.keys():
            self.spotSpectra.wxyImage = container1['image']
        if 'arr_1' in container1.keys():
            self.spotSpectra.wxyImage = container1['arr_1'] # b-c
        if 'wavelength' in container1.keys():      
            self.pF.wavelength = container1['wavelength']
        if 'arr_2' in container1.keys():      
            self.pF.wavelength = container1['arr_2'] # b-c

    def saveFitFile(self,folder,fileMainName):
        ''' save fit file'''
        np.savez(str(folder) + '/' +  str(fileMainName) + self.DEFAULT['nameSet']['fit'],
        pxBcg = self.spotSpectra.pxBcg,
        pxAve = self.spotSpectra.pxAve,
        pxSpace = self.spotSpectra.pxSpace,
        darkCount = self.spotSpectra.darkCount,
        wavelengthStartFit = self.pF.wavelengthStartFit,
        wavelengthStopFit = self.pF.wavelengthStopFit,
        orderFit = self.pF.orderFit,
        wavelengthGuess = self.pF.wavelengthGuess,
        peakWidth = self.pF.peakWidth
        )

    def loadFitFile(self,folder,fileMainName):
        ''' load fit file'''

        _file = Path(folder + '/' + fileMainName + self.DEFAULT['nameSet']['fit'])        
        if not _file.is_file():
            print(f'could not find file {_file}')
            return

        container1 = np.load(_file)
        if 'pxBcg' in container1.keys():
            self.spotSpectra.pxBcg = container1['pxBcg']
        if 'pxAve' in container1.keys():
            self.spotSpectra.pxAve = container1['pxAve'] 
        if 'pxSpace' in container1.keys():
            self.spotSpectra.pxSpace = container1['pxSpace']
        if 'darkCount' in container1.keys():
            self.spotSpectra.darkCount = container1['darkCount'] 
        if 'wavelengthStartFit' in container1.keys():      
            self.pF.wavelengthStartFit = container1['wavelengthStartFit']
        if 'wavelengthStopFit' in container1.keys():      
            self.pF.wavelengthStopFit = container1['wavelengthStopFit']
        if 'orderFit' in container1.keys():      
            self.pF.orderFit = container1['orderFit']
        if 'wavelengthGuess' in container1.keys():      
            self.pF.wavelengthGuess = container1['wavelengthGuess']
        if 'peakWidth' in container1.keys():      
            self.pF.peakWidth = container1['peakWidth']

    def saveSpotFile(self,folder,fileMainName):
        ''' save spot Data file'''
        np.savez(str(folder) + '/' +  str(fileMainName) + self.DEFAULT['nameSet']['spot'],
        signal = self.spotData.signal,
        time = self.spotData.time)            

    def loadSpotFile(self,folder,fileMainName):
        ''' load spot Data file'''
        _file = Path(folder + '/' + fileMainName + self.DEFAULT['nameSet']['spot'])        
        if not _file.is_file():
            print(f'could not find file {_file}')
            return

        container1 = np.load(_file)
        if 'signal' in container1.keys():
            self.spotData.signal = container1['signal']
        if 'arr_0' in container1.keys():
            self.spotData.signal = container1['arr_0'] # b-c
        if 'time' in container1.keys():
            self.spotData.time = container1['time']
        if 'arr_1' in container1.keys():
            self.spotData.time = container1['arr_1'] # b-c

    def saveFlowFile(self,folder,fileMainName):
        ''' save flow Data file'''
        np.savez(str(folder) + '/' +  str(fileMainName)  + self.DEFAULT['nameSet']['flow'],
        signal = self.flowData.signal,
        time = self.flowData.time)

    def loadFlowFile(self,folder,fileMainName):
        ''' load flow Data file'''
        _file = Path(folder + '/' + fileMainName + self.DEFAULT['nameSet']['flow'])        
        if not _file.is_file():
            print(f'could not find file {_file}')
            return

        container1 = np.load(_file)
        if 'signal' in container1.keys():
            self.flowData.signal = container1['signal']
        if 'arr_0' in container1.keys():
            self.flowData.signal = container1['arr_0'] # b-c
        if 'time' in container1.keys():
            self.flowData.time = container1['time']
        if 'arr_1' in container1.keys():
            self.flowData.time = container1['arr_1'] # b-c

    def saveInfoFile(self,folder,fileMainName):
        ''' save Info Data file'''
        with open(str(folder) + '/' +  str(fileMainName)  + self.DEFAULT['nameSet']['info'],'wb') as f:
            pickle.dump((self.spotData.table,
                         self.spotData.alignTime,
                         self.spotData.range,
                         self.spotData.evalTime,
                         self.spotData.dTime)
                         ,f)

    def loadInfoFile(self,folder,fileMainName):
        ''' load info into the class from file'''
        _file = Path(folder + '/' + fileMainName + self.DEFAULT['nameSet']['info'])        
        if not _file.is_file():
            print(f'could not find file {_file}')
            return
        with open(_file, 'rb') as f:
            (self.spotData.table,
             self.spotData.alignTime,
             self.spotData.range,
             self.spotData.evalTime,
             self.spotData.dTime) = pickle.load(f) 

    def saveAllFile(self,folder,fileMainName):
        ''' save all data'''
        self.saveImageFile(folder,fileMainName)
        self.saveFitFile(folder,fileMainName)
        self.saveFlowFile(folder,fileMainName)
        self.saveSpotFile(folder,fileMainName)
        self.saveInfoFile(folder,fileMainName)

    def loadAllFile(self,folder,fileMainName):
        ''' save all data'''
        self.loadImageFile(folder,fileMainName)
        self.loadFitFile(folder,fileMainName)
        self.loadFlowFile(folder,fileMainName)
        self.loadSpotFile(folder,fileMainName)
        self.loadInfoFile(folder,fileMainName)





#%%

# TODO: test it!
if __name__ == '__main__':
    pass

'''
class for tracking of plasmon peaks
'''
#%%
from pathlib import Path
import numpy as np

from viscope.gui.baseGUI import BaseGUI
from magicgui import magicgui, widgets
from plim.algorithm.fileData import FileData


class SaveDataGUI(BaseGUI):
    ''' main class to save data'''

    DEFAULT = {'nameGUI': 'Data'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # prepare the gui of the class
        SaveDataGUI.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        @magicgui(filePath={"label": "Saving file Path:","mode":'d'},
                fileName={"label": "Saving file Name:"},
                call_button="Save")
        def saveGui(filePath= Path(self.viscope.dataFolder), fileName: str = 'Experiment1'):

            _fileData = FileData(spotData=self.device.spotData,
                                 flowData=self.device.flowData,
                                 spotSpectra=self.device.spotSpectra,
                                 plasmonFit=self.device.pF)
            
            _fileData.saveAllFile(folder=filePath,fileMainName=fileName)

        @magicgui(call_button="Reset")
        def resetGui():
            self.device.spotData.clearData()
            self.device.flowData.clearData()

        # add widgets 

        container = widgets.Container(
        widgets=[saveGui, resetGui], layout="vertical", labels=False)
        self.dataGui = container
        self.vWindow.addParameterGui(self.dataGui,name=self.DEFAULT['nameGUI'])
 

if __name__ == "__main__":
    pass



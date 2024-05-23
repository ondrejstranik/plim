'''
class for tracking of plasmon peaks
'''
#%%
from pathlib import Path
import numpy as np

from viscope.gui.baseGUI import BaseGUI
from magicgui import magicgui

class SaveDataGUI(BaseGUI):
    ''' main class to save data'''

    DEFAULT = {'nameGUI': 'Save Data'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # prepare the gui of the class
        SaveDataGUI.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        @magicgui(filePath={"label": "Saving file Path:","mode":'d'},
                fileName={"label": "Saving file Name:"})
        def saveGui(filePath= Path(self.viscope.dataFolder), fileName: str = 'Experiment1'):

            np.savez(str(filePath / fileName) + '_spotData',self.device.spotData.signal,self.device.spotData.time)            
            np.savez(str(filePath / fileName) + '_flowData',self.device.flowData.signal,self.device.flowData.time)            
            np.savez(str(filePath / fileName) + '_image',
            self.device.spotSpectra.spotPosition,
            self.device.spotSpectra.wxyImage,
            self.device.pF.wavelength)            


        # add widgets 
        self.saveGui = saveGui
        self.vWindow.addParameterGui(self.saveGui,name=self.DEFAULT['nameGUI'])
 

if __name__ == "__main__":
    pass



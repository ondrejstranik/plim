'''
class for tracking of plasmon peaks
'''
#%%
from pathlib import Path
import numpy as np

from viscope.gui.baseGUI import BaseGUI
from magicgui import magicgui, widgets

class SaveDataGUI(BaseGUI):
    ''' main class to save data'''

    DEFAULT = {'nameGUI': 'Data',
               'nameSet'  : {
                            'flow':'_flowData.npz',
                            'image': '_image.npz',
                            'spot': '_spotData.npz',
                            'fit': '_fit.npz',
                            'info': '_info.dat'
                            }
            }

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

            np.savez(str(filePath / fileName) + self.DEFAULT['spot'],self.device.spotData.signal,self.device.spotData.time)            
            np.savez(str(filePath / fileName) + self.DEFAULT['flow'],self.device.flowData.signal,self.device.flowData.time)            
            np.savez(str(filePath / fileName) + self.DEFAULT['image'],
            self.device.spotSpectra.spotPosition,
            self.device.spotSpectra.wxyImage,
            self.device.pF.wavelength)
            np.savez(str(filePath / fileName) + self.DEFAULT['fit'],
            pxBcg = self.device.spotSpectra.pxBcg,
            pxAve = self.device.spotSpectra.pxAve,
            pxSpace = self.device.spotSpectra.pxSpace,
            darkCount = self.device.spotSpectra.darkCount,
            wavelengthStartFit = self.device.pF.wavelengthStartFit,
            wavelengthStopFit = self.device.pF.wavelengthStopFit,
            orderFit = self.device.pF.orderFit,
            wavelengthGuess = self.device.pF.wavelengthGuess,
            peakWidth = self.device.pF.peakWidth                        
            )

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



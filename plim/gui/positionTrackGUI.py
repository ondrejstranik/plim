'''
class for tracking of plasmon peaks
'''
#%%


from viscope.gui.baseGUI import BaseGUI
from plim.gui.signalViewer.signalWidget  import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
#from qtpy.QtWidgets import QVBoxLayout



class PositionTrackGUI(BaseGUI):
    ''' main class to show time evolution of plasmon peak position'''

    DEFAULT = {'nameGUI': 'Plasmon Signal'}


    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        # widget
        self.positionTrack = None
        self.flowTrack = None

        # prepare the gui of the class
        PositionTrackGUI.__setWidget(self) 

    def __setWidget(self):
        ''' prepare the gui '''

        # add widgets 
        self.positionTrack = SignalWidget()
        self.flowTrack = FlowRateWidget()

        #self.vWindow.addMainGUI(self.positionTrack,name=self.DEFAULT['nameGUI'])
        self.vWindow.addParameterGui(self.positionTrack,name=self.positionTrack.DEFAULT['nameGUI'])
        self.vWindow.addParameterGui(self.flowTrack,name=self.flowTrack.DEFAULT['nameGUI'])




    def setDevice(self,device):
        super().setDevice(device)
        # connect data container with device container
        self.positionTrack.sD = self.device.spotData
        self.flowTrack.flowData = self.device.flowData

        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)

    def updateGui(self):
        ''' update the data in gui '''
        self.positionTrack.drawGraph()
        self.flowTrack.drawGraph()

  

if __name__ == "__main__":
    pass



'''
class for tracking of plasmon peaks
'''
#%%


from viscope.gui.baseGUI import BaseGUI
from plim.gui.signalViewer.signalWidget  import SignalWidget
from plim.gui.signalViewer.flowRateWidget import FlowRateWidget
from plim.gui.signalViewer.injectionWidget import InjectionWidget
from plim.gui.signalViewer.infoWidget import InfoWidget
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
        self.infoWidget = None

        # prepare the gui of the class
        PositionTrackGUI.__setWidget(self)

    def __setWidget(self):
        ''' prepare the gui '''

        # add widgets
        self.positionTrack = SignalWidget()
        self.flowTrack = FlowRateWidget()
        self.injectionTrack = InjectionWidget()
        self.infoWidget = InfoWidget()

        #self.vWindow.addMainGUI(self.positionTrack,name=self.DEFAULT['nameGUI'])
        self.vWindow.addParameterGui(self.positionTrack,name=self.positionTrack.DEFAULT['nameGUI'])
        self.vWindow.addParameterGui(self.flowTrack,name=self.flowTrack.DEFAULT['nameGUI'])
        self.vWindow.addParameterGui(self.injectionTrack,name=self.injectionTrack.DEFAULT['nameGUI'])
        self.vWindow.addParameterGui(self.infoWidget,name=self.infoWidget.DEFAULT['nameGUI'])

        # keep the signal graph in sync with edits made in the info table (color/visible/...)
        self.infoWidget.sigUpdateData.connect(self.positionTrack.redrawWidget)

        # select the same row in the info table when the line selection changes in positionTrack
        self.positionTrack.sigUpdateData.connect(self.updateInfoSelectionFromSignal)

        # update the injection time input when the eval time marker (vLine[0]) is moved
        self.positionTrack.vLine[0].sigPositionChanged.connect(self.updateInjectionTimeInput)

        # mirror the first two vLine markers of positionTrack onto flowTrack
        for ii in range(2):
            self.positionTrack.vLine[ii].sigPositionChanged.connect(
                lambda _, ii=ii: self.flowTrack.vLine[ii].setPos(self.positionTrack.vLine[ii].value()))

        # allow the same '1'/'2' keyboard shortcuts to move the markers from flowTrack
        self.flowTrack.sigSetEvalTime.connect(self.setEvalTimeFromFlow)
        self.flowTrack.sigSetDTime.connect(self.setDTimeFromFlow)

    def setEvalTimeFromFlow(self,value):
        ''' set evalTime in positionTrack, triggered from a key press in flowTrack '''
        self.positionTrack.lineParameter.evalTime.value = value

    def setDTimeFromFlow(self,value):
        ''' set dTime in positionTrack, triggered from a key press in flowTrack '''
        value = value - self.positionTrack.sD.evalTime
        if value < 0: value = 0
        self.positionTrack.lineParameter.dTime.value = value

    def updateInjectionTimeInput(self):
        ''' set the injectionInfo time input to the position of vLine[0] '''
        self.injectionTrack.timeInput.setText(str(int(self.positionTrack.vLine[0].value())))

    def updateInfoSelectionFromSignal(self):
        ''' select the same row in the info table as the line currently selected in positionTrack '''
        self.infoWidget.updateSelect(self.positionTrack.lineIndex)

    def interconnectGui(self,plasmonViewerGUI=None):
        ''' connect with other gui'''
        self.pvGui = plasmonViewerGUI

        # share the same table dict by identity - a mutation via either name
        # is instantly visible through the other. Relies on SpotData.
        # setTable()/clearData() and InfoWidget._syncFromTable() mutating
        # self.table in place rather than rebinding it (see spotData.py/
        # infoWidget.py) - otherwise this alias would silently break the
        # first time either fires.
        self.pvGui.plasmonViewer.table = self.positionTrack.sD.table

        # connect signals
        self.positionTrack.sigUpdateData.connect(self.pvGui.plasmonViewer.syncPointsFromTable)
        self.infoWidget.sigUpdateData.connect(self.pvGui.plasmonViewer.syncPointsFromTable)
        self.pvGui.plasmonViewer.sigUpdateData.connect(self.onPlasmonViewerChanged)
        self.pvGui.plasmonViewer.sigColorChanged.connect(self.onPlasmonViewerChanged)
        self.pvGui.plasmonViewer.sigSelectionChanged.connect(self.updateInfoSelectionFromPlasmonViewer)

    def setDevice(self,device):
        super().setDevice(device)
        # connect data container with device container
        self.positionTrack.sD = self.device.spotData
        # spotData carries no spot coordinates - FitWidget's 'transfer data'
        # button pulls them straight from here (via SignalWidget) instead
        self.positionTrack.spotSpectra = self.device.spotSpectra
        self.flowTrack.flowData = self.device.flowData
        self.injectionTrack.iD = self.device.injectionData
        self.infoWidget.sD = self.device.spotData

        # connect signals - FileDataProcessor (offline review) never starts a
        # worker thread, so there is nothing to poll for it
        if self.device.worker is not None:
            self.device.worker.yielded.connect(self.guiUpdateTimed)

    def onPlasmonViewerChanged(self):
        ''' resync SignalWidget/InfoWidget's cached widgets and redraw after the
        plasmon viewer changed the shared table - fired by sigUpdateData (point
        add/move/delete) and sigColorChanged (a point's color changed). The
        table mutation itself already happened at the source, in
        SViewer.pointChanged()/colorChanged(), since plasmonViewer.table IS
        positionTrack.sD.table - nothing left to reconstruct here.

        resync (not redrawWidget() - that also touches evalTime/dTime, which
        could race with the '1'/'2' keyboard shortcuts) so lineParameter's
        cached visible/name/color don't go stale and get misread as real
        changes next time lineParameter runs '''
        self.positionTrack.resyncLineTableWidgets()
        self.positionTrack.drawGraph()
        self.infoWidget.redrawWidget()

    def updateInfoSelectionFromPlasmonViewer(self):
        ''' select the same rows in the info table when spots are selected in the plasmon viewer '''
        idx = list(self.pvGui.plasmonViewer.pointLayer.selected_data)
        self.infoWidget.updateSelect(idx)

    def updateGui(self):
        ''' update the data in gui '''

        # update the graph
        self.positionTrack.drawGraph()
        self.flowTrack.drawGraph()
        self.injectionTrack.updateEditor()
        self.infoWidget.redrawWidget()

  

if __name__ == "__main__":
    pass



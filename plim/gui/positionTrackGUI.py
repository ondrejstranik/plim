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
import traceback


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

        # connect signals
        self.positionTrack.sigUpdateData.connect(self.updatePlasmonViewer)
        self.infoWidget.sigUpdateData.connect(self.updatePlasmonViewer)
        self.pvGui.plasmonViewer.sigUpdateData.connect(self.updatePositionTrack)
        self.pvGui.plasmonViewer.sigColorChanged.connect(self.updatePositionTrackColor)
        self.pvGui.plasmonViewer.sigSelectionChanged.connect(self.updateInfoSelectionFromPlasmonViewer)

    def setDevice(self,device):
        super().setDevice(device)
        # connect data container with device container
        self.positionTrack.sD = self.device.spotData
        self.flowTrack.flowData = self.device.flowData
        self.injectionTrack.iD = self.device.injectionData
        self.infoWidget.sD = self.device.spotData

        # connect signals
        self.device.worker.yielded.connect(self.guiUpdateTimed)

    def updatePlasmonViewer(self):
        ''' update plasmonViewer because data in position track changed '''
        if self.pvGui is None:
            return

        # no data received yet - nothing to push to the viewer
        rgb = self.positionTrack.sD.table['color']
        if rgb is None:
            return

        vis = self.positionTrack.sD.table['visible']
        _color = [rgb[ii] + 'ff' if vis[ii]=='True' else rgb[ii] + '00' for ii in range(len(rgb))]

        self.pvGui.plasmonViewer.pointLayer.face_color = _color

        # keep the point annotations in sync with the (possibly renamed) spots
        try:
            self.pvGui.plasmonViewer.pointLayer.features = {'names': self.positionTrack.sD.table['name']}
        except:
            print('error updating plasmonViewer point annotations')
            traceback.print_exc()

    def updatePositionTrack(self):
        ''' update spotData because the number/position of spots changed in the plasmon viewer '''

        try:
            _fcHex = ['#{:02x}{:02x}{:02x}'.format( *ii.tolist())
                      for ii in (self.pvGui.plasmonViewer.pointLayer.face_color*255).astype(int)]

            # keep name/visible consistent with the (possibly changed) number of
            # points, so the table stays internally consistent immediately -
            # otherwise a point add/delete would leave 'color' resized to the
            # new spot count while 'name'/'visible' are still the old length
            nSpot = len(_fcHex)
            _oldName = self.positionTrack.sD.table.get('name') or []
            _oldVisible = self.positionTrack.sD.table.get('visible') or []
            self.positionTrack.sD.table['name'] = [_oldName[ii] if ii < len(_oldName) else str(ii) for ii in range(nSpot)]
            self.positionTrack.sD.table['visible'] = [_oldVisible[ii] if ii < len(_oldVisible) else 'True' for ii in range(nSpot)]
            self.positionTrack.sD.table['color'] = _fcHex
        except:
            print('error in updatePositionTrack')
            traceback.print_exc()
            return

        # don't rely on the periodic updateGui() tick - it only runs when new
        # data arrives from the device, which may be paused/idle (e.g. when
        # reviewing a recorded file-based dataset rather than a live camera)
        self.positionTrack.drawGraph()
        self.infoWidget.redrawWidget()

    def updatePositionTrackColor(self):
        ''' update color in spotData because a point's color was changed in the plasmon viewer '''

        try:
            _fc = 1*self.pvGui.plasmonViewer.pointLayer.face_color #  deep copy of the colors
            _fc[list(self.pvGui.plasmonViewer.pointLayer.selected_data)] = self.pvGui.plasmonViewer.pointLayer._face.current_color # adjust the just modified
            _fcHex = ['#{:02x}{:02x}{:02x}'.format( *ii.tolist()) for ii in (_fc*255).astype(int)]
            self.positionTrack.sD.table['color'] = _fcHex
        except:
            print('error in updatePositionTrackColor')
            traceback.print_exc()
            return

        # don't rely on the periodic updateGui() tick - see updatePositionTrack()
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



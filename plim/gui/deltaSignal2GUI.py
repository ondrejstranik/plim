'''
class for pushing a delta-signal image layer into the offline signal analyser
'''
#%%
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton

from viscope.gui.baseGUI import BaseGUI
from plim.gui.deltaSignalGUI import DeltaSignalGUI


class DeltaSignal2GUI(DeltaSignalGUI):
    ''' offline counterpart of DeltaSignalGUI, for the signal analyser
    (FileDataProcessor, which never starts a worker thread - so there is
    no periodic tick driving updates, and no "latest recorded time" that
    keeps moving for dTime to grow toward once a dataset is loaded).

    Reuses everything from DeltaSignalGUI except:
    - no 'dtime update' tick - it would have nothing meaningful to do,
      since there's no live data arriving to grow dTime toward. Always
      just follows whatever evalTime/dTime SignalWidget currently shows.
    - interconnectGui() connects SignalWidget's sigUpdateData straight to
      updateGui(), unthrottled - with no worker there is no later tick to
      catch a rate-limited edit, so it must never be silently dropped
      (see DeltaSignalGUI.interconnectGui() for the live-side reasoning
      on why routing through guiUpdateTimed() is fine there but not here). '''

    DEFAULT = {'nameGUI': 'DeltaSignal'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class - deliberately calls BaseGUI.__init__()
        directly (not DeltaSignalGUI.__init__()), since that would also
        run DeltaSignalGUI.__setWidget() and build the 'dtime update'
        tick this class doesn't use '''
        BaseGUI.__init__(self, viscope, **kwargs)

        self.device = None
        self.viewerGui = None
        self.ptGui = None
        self.liveLayer = None  # the reusable 'liveDelta' napari image layer

        DeltaSignal2GUI.__setWidget(self)

    def __setWidget(self):
        ''' prepare the gui - same as DeltaSignalGUI but without the
        'dtime update' tick '''

        plotBtn = QPushButton('new Image')
        plotBtn.clicked.connect(self.plotDeltaSignal)

        self.liveBtn = QPushButton('live Image')
        self.liveBtn.setCheckable(True)
        self.liveBtn.toggled.connect(self._onLiveToggled)

        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(plotBtn)
        layout.addWidget(self.liveBtn)
        self.widget.setLayout(layout)

        self.vWindow.addParameterGui(self.widget, name=self.DEFAULT['nameGUI'])

    def interconnectGui(self, viewerGui, ptGui=None):
        ''' connect with the viewer GUI (e.g. SpotViewerGUI) whose napari
        window the delta-signal layer(s) get added into, and optionally
        with PositionTrackGUI so 'liveDelta' refreshes whenever
        SignalWidget's own lineParameter fires sigUpdateData (e.g. on
        every evalTime/dTime edit). Connected directly to updateGui(),
        not guiUpdateTimed() - there is no worker tick offline to catch a
        rate-limited edit later, so it must never be silently dropped. '''
        self.viewerGui = viewerGui
        self.ptGui = ptGui
        if self.ptGui is not None:
            self.ptGui.positionTrack.sigUpdateData.connect(self.updateGui)

    def _updateLiveDelta(self):
        ''' push the delta signal at whatever evalTime/dTime SignalWidget
        currently shows into the reusable 'liveDelta' layer - a pure,
        non-mutating computeDSignal() read, same as DeltaSignalGUI's
        'dtime update' unchecked behaviour, but unconditional here since
        there is no auto-growing alternative offline. '''
        sD = self.device.spotData
        if sD.time is None or len(sD.time) == 0:
            return

        dSignal = sD.computeDSignal(sD.evalTime, sD.dTime)

        _image = self._buildDeltaImage(dSignal)
        if _image is None:
            return

        if self.liveLayer is None or self.liveLayer not in self.viewerGui.viewer.layers:
            self.liveLayer = self.viewerGui.viewer.add_image(_image, name='liveDelta', colormap='turbo')
        else:
            self.liveLayer.data = _image


if __name__ == "__main__":
    pass

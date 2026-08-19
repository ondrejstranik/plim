'''
thin wrapper GUI for FitWidget - kinetic fitting of a completed signal curve
'''
#%%
from viscope.gui.baseGUI import BaseGUI
from plim.gui.signalViewer.fitWidget import FitWidget


class FitGUI(BaseGUI):
    ''' GUI wrapping FitWidget for the offline signal analyser. offline-analysis-only
    (kinetic fitting on a completed curve, no use case during live acquisition), so
    kept separate from PositionTrackGUI '''

    DEFAULT = {'nameGUI': 'Fit'}

    def __init__(self, viscope, **kwargs):
        ''' initialise the class '''
        super().__init__(viscope, **kwargs)

        FitGUI.__setWidget(self)

    def __setWidget(self):
        ''' prepare the gui '''

        self.fitWidget = FitWidget()
        self.vWindow.addParameterGui(self.fitWidget, name=self.DEFAULT['nameGUI'])

    def interconnectGui(self, ptGui):
        ''' connect with PositionTrackGUI - the fit widget pulls signal/time
        data from its SignalWidget on demand '''
        self.fitWidget.connectDataObject(ptGui.positionTrack)


if __name__ == "__main__":
    pass

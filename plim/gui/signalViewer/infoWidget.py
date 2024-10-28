'''
class for viewing info from spots' plasmon resonance
'''

import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget,QVBoxLayout
from qtpy.QtCore import Signal
from magicgui import magicgui

import numpy as np
from plim.algorithm.spotInfo import SpotInfo


class InfoWidget(QWidget):
    ''' main class for viewing signal'''
    DEFAULT = {'nameGUI':'Signal'}

    sigUpdateData = Signal()

    def __init__(self, **kwargs):
        ''' initialise the class '''
        super().__init__()

        self.sI = SpotInfo()

        # set this gui of this class
        InfoWidget._setWidget(self)


    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(auto_call=True,
                  infoTable = {'widget_type':'Table'})
        def infoBox(
            infoTable: dict = self.sI.table
            ):
            self.infoBox._auto_call = False
            self.sI.table = dict(infoBox.infoTable).copy()
            self.sI.checkValues()
            infoBox.infoTable.value = self.sI.table.copy()
            self.infoBox._auto_call = True

            print(dict(infoBox.infoTable))
            self.sigUpdateData.emit()
            print('emitting signal')

        # fit parameter
        self.infoBox = infoBox

        layout = QVBoxLayout()
        layout.addWidget(self.infoBox.native)
        self.setLayout(layout)

    def updateData(self):
        _temp =  self.infoBox._auto_call
        self.infoBox._auto_call = False
        self.infoBox.infoTable.value = self.sI.table.copy()
        self.infoBox._auto_call = _temp
        self.sigUpdateData.emit()
        print('emitting signal')

if __name__ == "__main__":
    pass

        















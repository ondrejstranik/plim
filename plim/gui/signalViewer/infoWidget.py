'''
class for viewing info from spots' plasmon resonance
'''

import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget,QVBoxLayout
from qtpy.QtCore import Signal
from magicgui import magicgui

import numpy as np
#from plim.algorithm.spotData import SpotData
from plim.algorithm.spotData import SpotData


class InfoWidget(QWidget):
    ''' main class for viewing signal'''
    DEFAULT = {'nameGUI':'Signal'}

    sigUpdateData = Signal()

    def __init__(self, spotData = None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        self.sD = spotData if spotData is not None else SpotData(np.arange(10*3).reshape(10,3))

        # set this gui of this class
        InfoWidget._setWidget(self)


    def keyPressEvent(self, evt):
        ''' react on the key pressed, when focused on the widget'''
        _text = evt.text()

        if _text == 'v':
            indexes = self.infoBox.infoTable.native.selectionModel().selectedRows()
            _idx = [index.row() for index in indexes]
            print(f'selected rows in the table {_idx}')
            if _idx == []:
                self.setFocus()
                return 
            if self.sD.table['visible'][_idx[0]]=='True':
                for ii in _idx:
                    self.sD.table['visible'][ii] = 'False'
            else:
                for ii in _idx:
                    self.sD.table['visible'][ii] = 'True'

            self.updateData()
            # keep the keyPressEvent on the this signal widget
            self.setFocus()


    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(auto_call=True,
                  infoTable = {'widget_type':'Table'})
        def infoBox(
            infoTable: dict = self.sD.table | {'dSignal': self.sD.dSignal, 'noise': self.sD.noise}
            ):
            self.infoBox._auto_call = False
            #self.sD.table = dict(infoBox.infoTable).copy()
            self.sD.table = dict(infoBox.infoTable)
            self.sD.checkTableValues()
            #infoBox.infoTable.value = self.sD.table.copy()
            infoBox.infoTable.value = self.sD.table | {'dSignal': self.sD.dSignal, 'noise': self.sD.noise}
            self.infoBox._auto_call = True

            #print(dict(infoBox.infoTable))
            self.sigUpdateData.emit()
            print('infoWidget: emitting signal')

        # fit parameter
        self.infoBox = infoBox
        #self.infoBox.infoTable.native.setSelectionMode(4)

        layout = QVBoxLayout()
        layout.addWidget(self.infoBox.native)
        self.setLayout(layout)

    def updateData(self):
        _temp =  self.infoBox._auto_call
        self.infoBox._auto_call = False
        
        _dict = {'dSignal': self.sD.dSignal, 'noise': self.sD.noise}

        #self.infoBox.infoTable.value = self.sD.table.copy()
        self.infoBox.infoTable.value = self.sD.table | _dict

        
        self.infoBox._auto_call = _temp
        self.sigUpdateData.emit()
        print('emitting signal')

    def updateSelect(self,idx):
        print(f'row to select : {idx}')

        #idx = np.array(idx, ndmin=1)
        self.infoBox.infoTable.native.selectionModel().clear()
        self.infoBox.infoTable.native.selectRow(idx)

        #self.infoBox.infoTable.native.selectionModel().clear()
        #self.infoBox.infoTable.native.setSelectionMode(4)
        #for ii in idx:
        #    if ii is not None:
        #        self.infoBox.infoTable.native.selectRow(ii)
        #self.infoBox.infoTable.native.setSelectionMode(1)
        #indexes = self.infoBox.infoTable.native.selectionModel().selectedRows()
        #for index in sorted(indexes):
        #    print('Row %d is selected' % index.row())


if __name__ == "__main__":
    pass

        















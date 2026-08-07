'''
class for viewing info from spots' plasmon resonance
'''

import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget,QVBoxLayout
from qtpy.QtCore import Signal, Qt
from magicgui import magicgui

import numpy as np
#from plim.algorithm.spotData import SpotData
from plim.algorithm.spotData import SpotData


class InfoWidget(QWidget):
    ''' main class for viewing signal'''
    DEFAULT = {'nameGUI':'Signal',
               # columns shown in the info table that are computed/reference
               # values and must not be overwritten by the (text-only) table
               # widget content
               'notEditableColumn': ['position', 'dSignal', 'noise']}

    sigUpdateData = Signal()

    def __init__(self, spotData = None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        self.sD = spotData if spotData is not None else SpotData(np.arange(10*3).reshape(10,3))

        # set this gui of this class
        InfoWidget._setWidget(self)

    def _displayTable(self):
        ''' dict shown in the info table widget, including read-only columns '''
        return self.sD.table | {'dSignal': self.sD.dSignal, 'noise': self.sD.noise}

    def _styleNonEditableColumns(self):
        ''' grey out and lock the non-editable columns in the info table '''
        columns = list(self._displayTable().keys())
        table = self.infoBox.infoTable.native
        for key in self.DEFAULT['notEditableColumn']:
            if key not in columns:
                continue
            col = columns.index(key)
            for row in range(table.rowCount()):
                item = table.item(row, col)
                if item is None:
                    continue
                item.setBackground(QColor('lightgray'))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)


    def keyPressEvent(self, evt):
        ''' react on the key pressed, when focused on the widget'''
        _text = evt.text()
        #_key = evt.key()

        #TODO: shortcuts goes to name collums. Avoid it before activating shortcuts
        #if _text == 'v':
        if False:
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

            # keep the keyPressEvent on the this signal widget
            self.setFocus()

            self.redrawWidget()
            # emit signal to eventually update data in other guis
            self.sigUpdateData.emit()


    def _setWidget(self):
        ''' prepare the gui '''

        @magicgui(auto_call=True,
                  infoTable = {'widget_type':'Table'})
        def infoBox(
            infoTable: dict = self._displayTable()
            ):
            self.infoBox._auto_call = False

            # non-editable columns hold computed/reference values; the table
            # widget only stores displayed text, so reading them back would
            # corrupt values like the position arrays into their string repr
            _notEditable = {key: self.sD.table[key] for key in self.DEFAULT['notEditableColumn']
                             if key in self.sD.table}
            self.sD.table = dict(self.infoBox.infoTable)
            for key in self.DEFAULT['notEditableColumn']:
                self.sD.table.pop(key, None)
            self.sD.table |= _notEditable

            #print(f'sD.table from infoBox {self.sD.table}')


            self.sD.checkTableValues()

            # update values in the case color is changed
            self.sD.setReference()
            self.sD.getDSignal()
            self.sD.getNoise()

            self.infoBox.infoTable.value = self._displayTable()

            for ii,_color in enumerate(self.sD.table['color']):
                self.infoBox.infoTable.native.item(ii,1).setBackground(QColor(_color))
            self._styleNonEditableColumns()

            self.infoBox._auto_call = True

            # emit signal to eventually update data in other guis
            self.sigUpdateData.emit()


        # fit parameter
        self.infoBox = infoBox
        self.infoBox.infoTable.native.setSelectionMode(4)
        self.redrawWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.infoBox.native)
        self.setLayout(layout)

    def redrawWidget(self):
        ''' redraw all values in the widget from class parameters'''
        
        # switch off auto_call 
        _temp =  self.infoBox._auto_call
        self.infoBox._auto_call = False
        # update values
        self.infoBox.infoTable.value = self._displayTable()
        
        for ii,_color in enumerate(self.sD.table['color']):
            self.infoBox.infoTable.native.item(ii,1).setBackground(QColor(_color))
        self._styleNonEditableColumns()

        # switch auto_call on initial value
        self.infoBox._auto_call = _temp

    def updateSelect(self,idx):
        print(f'row to select : {idx}')

        idx = np.array(idx, ndmin=1)

        self.infoBox.infoTable.native.selectionModel().clear()
        self.infoBox.infoTable.native.setSelectionMode(2)
        for ii in idx:
            if ii is not None:
                self.infoBox.infoTable.native.selectRow(ii)
        self.infoBox.infoTable.native.setSelectionMode(4)

if __name__ == "__main__":
    pass

        















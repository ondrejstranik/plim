'''
class for viewing info from spots' plasmon resonance
'''

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QWidget,QVBoxLayout,QTableWidget,QTableWidgetItem,QAbstractItemView
from qtpy.QtCore import Signal, Qt, QItemSelectionModel

import numpy as np
from plim.algorithm.spotData import SpotData


class _InfoTable(QTableWidget):
    ''' QTableWidget that keeps an existing multi-cell selection when the
    user clicks (e.g. to start editing) on a cell that is already part of
    it, instead of collapsing the selection down to that single cell '''

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if (index.isValid() and len(self.selectedItems()) > 1
                and self.selectionModel().isSelected(index)):
            # move the current index (so double-click edits this cell) without
            # touching the selection - QAbstractItemView.setCurrentIndex()
            # would otherwise collapse the multi-cell selection down to this one
            self.selectionModel().setCurrentIndex(index, QItemSelectionModel.NoUpdate)
            return
        super().mousePressEvent(event)


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

    def keyPressEvent(self, evt):
        ''' react on the key pressed, when focused on the widget'''
        _text = evt.text()
        #_key = evt.key()

        #TODO: shortcuts goes to name collums. Avoid it before activating shortcuts
        #if _text == 'v':
        if False:
            indexes = self.infoTable.selectionModel().selectedRows()
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

        self.infoTable = _InfoTable()
        self.infoTable.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.infoTable.itemChanged.connect(self._onItemChanged)

        layout = QVBoxLayout()
        layout.addWidget(self.infoTable)
        self.setLayout(layout)

        self.redrawWidget()

    def _onItemChanged(self, item):
        ''' react on a single cell edit; if several cells in the same column
        are selected, apply the same typed value to all of them
        (spreadsheet-like fill) '''
        columns = list(self._displayTable().keys())
        if columns[item.column()] in self.DEFAULT['notEditableColumn']:
            return

        # only fill cells in the same column as the edited one, so selecting
        # whole rows and editing one column doesn't overwrite other columns
        selected = [cell for cell in self.infoTable.selectedItems()
                    if cell.column() == item.column()]
        if item in selected and len(selected) > 1:
            newValue = item.text()
            self.infoTable.blockSignals(True)
            for cell in selected:
                cell.setText(newValue)
            self.infoTable.blockSignals(False)

        self._syncFromTable()

    def _syncFromTable(self):
        ''' read the table widget content back into sD.table, recalculate and redraw '''
        columns = list(self._displayTable().keys())
        nRow = self.infoTable.rowCount()

        # non-editable columns hold computed/reference values; the table
        # widget only stores displayed text, so reading them back would
        # corrupt values like the position arrays into their string repr
        _notEditable = {key: self.sD.table[key] for key in self.DEFAULT['notEditableColumn']
                         if key in self.sD.table}

        newTable = {}
        for col, key in enumerate(columns):
            if key in self.DEFAULT['notEditableColumn']:
                continue
            newTable[key] = [self.infoTable.item(row, col).text() for row in range(nRow)]

        self.sD.table = newTable | _notEditable

        self.sD.checkTableValues()

        # update values in the case color is changed
        self.sD.setReference()
        self.sD.getDSignal()
        self.sD.getNoise()

        self.redrawWidget()

        # emit signal to eventually update data in other guis
        self.sigUpdateData.emit()

    def redrawWidget(self):
        ''' redraw all values in the widget from class parameters'''

        table = self._displayTable()
        columns = list(table.keys())
        nRow = len(self.sD.table['name'])

        self.infoTable.blockSignals(True)

        self.infoTable.setColumnCount(len(columns))
        self.infoTable.setRowCount(nRow)
        self.infoTable.setHorizontalHeaderLabels(columns)

        for col, key in enumerate(columns):
            values = table[key]
            notEditable = key in self.DEFAULT['notEditableColumn']
            for row in range(nRow):
                item = self.infoTable.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                    self.infoTable.setItem(row, col, item)
                item.setText(str(values[row]))
                if notEditable:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QColor('lightgray'))
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

        if 'color' in columns:
            colorCol = columns.index('color')
            for row, _color in enumerate(self.sD.table['color']):
                self.infoTable.item(row, colorCol).setBackground(QColor(_color))

        self.infoTable.blockSignals(False)

    def updateSelect(self,idx):
        print(f'row to select : {idx}')

        idx = np.array(idx, ndmin=1)

        self.infoTable.selectionModel().clear()
        self.infoTable.setSelectionMode(QAbstractItemView.MultiSelection)
        for ii in idx:
            if ii is not None:
                self.infoTable.selectRow(ii)
        self.infoTable.setSelectionMode(QAbstractItemView.ExtendedSelection)

if __name__ == "__main__":
    pass

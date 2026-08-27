'''
class for viewing info from spots' plasmon resonance
'''

import logging
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QWidget,QVBoxLayout,QTableWidget,QTableWidgetItem,QAbstractItemView
from qtpy.QtCore import Signal, Qt, QItemSelectionModel

import numpy as np
from plim.algorithm.spotData import SpotData

logger = logging.getLogger(__name__)


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
    DEFAULT = {'nameGUI':'Info',
               # columns shown in the info table that are computed/reference
               # values and must not be overwritten by the (text-only) table
               # widget content
               'notEditableColumn': ['dSignal', 'noise']}

    sigUpdateData = Signal()

    def __init__(self, spotData = None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        self.sD = spotData if spotData is not None else SpotData(np.arange(10*3).reshape(10,3))

        # display-order state for column-header double-click sorting.
        # _sortOrder[row] = underlying spot index shown at that display row
        # (None = natural/identity order). Rows are never physically moved
        # in sD.table itself - only how they're displayed/edited/selected
        # here is remapped through this permutation, so other widgets that
        # reference spots by their real index (SignalWidget.lineIndex,
        # PositionTrackGUI's viewer-click selection, ...) stay correct
        self._sortOrder = None
        self._sortColumn = None
        self._sortAscending = True

        # set this gui of this class
        InfoWidget._setWidget(self)

    def _displayTable(self):
        ''' dict shown in the info table widget, including read-only columns '''
        nRow = len(self.sD.table['name']) if self.sD.table.get('name') is not None else 0
        dSignal = self.sD.dSignal if self.sD.dSignal is not None else [None]*nRow
        noise = self.sD.noise if self.sD.noise is not None else [None]*nRow
        return self.sD.table | {'dSignal': dSignal, 'noise': noise}

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
        self.infoTable.horizontalHeader().sectionDoubleClicked.connect(self._onHeaderDoubleClicked)

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

    def _onHeaderDoubleClicked(self, col):
        ''' double-click a column header to sort rows by it - ascending,
        or descending if that same column is already sorted ascending '''
        self._sortAscending = not (self._sortColumn == col and self._sortAscending)
        self._sortColumn = col
        self._applySort()
        self._redrawTable()

    def _applySort(self):
        ''' recompute self._sortOrder (spot indices in display order) from
        self._sortColumn/_sortAscending against the current table data '''
        if self._sortColumn is None or self.sD.table.get('name') is None:
            return
        table = self._displayTable()
        columns = list(table.keys())
        if self._sortColumn >= len(columns):
            return
        values = table[columns[self._sortColumn]]
        nRow = len(self.sD.table['name'])

        def sortKey(i):
            # numeric compare when possible (so name '10' sorts after '2'),
            # falling back to text - keeps mixed/renamed columns usable
            try:
                return (0, float(values[i]))
            except (TypeError, ValueError):
                return (1, str(values[i]))

        self._sortOrder = sorted(range(nRow), key=sortKey, reverse=not self._sortAscending)

    def _displayOrder(self, nRow=None):
        ''' current display row -> spot index mapping, falling back to
        natural order if there's no sort yet or the spot count moved on
        since the last sort (e.g. after spot identification changed it).

        Pass nRow explicitly when the caller already holds a snapshot of
        sD.table (e.g. via _displayTable()) - re-reading
        len(self.sD.table['name']) independently here would reopen a race
        window against a concurrent table resize on another thread (e.g.
        SpotData.setTable(), called from the processing thread whenever
        the spot count changes): _redrawTable() computing nRow from one
        read and this method computing it from a second, later read could
        disagree, handing back indices out of range for the caller's own
        already-snapshotted data - which is exactly what previously
        crashed the app with an IndexError. '''
        if nRow is None:
            nRow = len(self.sD.table['name']) if self.sD.table.get('name') is not None else 0
        if self._sortOrder is not None and len(self._sortOrder) == nRow:
            return self._sortOrder
        self._sortOrder = None
        return list(range(nRow))

    def _syncFromTable(self):
        ''' read the table widget content back into sD.table, recalculate and redraw '''
        columns = list(self._displayTable().keys())
        nRow = self.infoTable.rowCount()
        order = self._displayOrder()

        if len(order) != nRow:
            # sD.table was resized on another thread (e.g. spot count
            # changed) between the widget being populated and this edit
            # landing - order no longer maps onto the widget's rows, so
            # writing back would scramble/IndexError. Discard this edit
            # and resync the display to the current true state instead
            logger.warning('info table row count changed mid-edit '
                            f'(widget has {nRow}, sD.table has {len(order)}) '
                            '- discarding edit and redrawing')
            self._redrawTable()
            return

        # non-editable columns hold computed/reference values; the table
        # widget only stores displayed text, so reading them back would
        # corrupt values like the position arrays into their string repr
        _notEditable = {key: self.sD.table[key] for key in self.DEFAULT['notEditableColumn']
                         if key in self.sD.table}

        newTable = {}
        for col, key in enumerate(columns):
            if key in self.DEFAULT['notEditableColumn']:
                continue
            # order[row] is the real spot index shown at this display row -
            # write it back there, not to `row`, so a sorted view doesn't
            # scramble which spot an edited value belongs to
            newColumn = [None] * nRow
            for row in range(nRow):
                newColumn[order[row]] = self.infoTable.item(row, col).text()
            newTable[key] = newColumn

        # mutate in place, don't rebind - keeps any external alias to
        # sD.table (e.g. a live viewer sharing it by reference) valid
        self.sD.table.clear()
        self.sD.table.update(newTable)
        self.sD.table.update(_notEditable)

        self.sD.checkTableValues()

        # update values in the case color is changed
        self.sD.setReference()
        self.sD.getDSignal()
        self.sD.getNoise()

        self._redrawTable()

        # emit signal to eventually update data in other guis
        self.sigUpdateData.emit()

    def redrawWidget(self):
        ''' redraw all values in the widget from class parameters.

        Skips the refresh while a cell is actively being edited, so
        periodic external updates (e.g. from a running acquisition) don't
        interrupt the user mid-edit. '''
        if self.infoTable.state() == QAbstractItemView.EditingState:
            return
        self._redrawTable()

    def _redrawTable(self):
        ''' unconditionally redraw all values in the table from sD '''

        if self.sD.table.get('name') is None:
            # no spots yet (e.g. acquisition just started, no data received)
            self.infoTable.setRowCount(0)
            return

        table = self._displayTable()
        columns = list(table.keys())
        # derive nRow from this snapshot, not a fresh self.sD.table read -
        # a concurrent SpotData.setTable() on the processing thread could
        # otherwise resize the live table between the two reads, handing
        # _displayOrder() a stale nRow that doesn't match `table` below
        nRow = len(table['name'])
        order = self._displayOrder(nRow)   # order[row] = spot index shown there

        self.infoTable.blockSignals(True)

        self.infoTable.setColumnCount(len(columns))
        self.infoTable.setRowCount(nRow)
        self.infoTable.setHorizontalHeaderLabels(columns)
        # vertical header shows the real spot index, so a sorted row is
        # still identifiable once its on-screen position no longer matches it
        self.infoTable.setVerticalHeaderLabels([str(ii) for ii in order])
        if self._sortColumn is not None:
            self.infoTable.horizontalHeader().setSortIndicator(
                self._sortColumn,
                Qt.AscendingOrder if self._sortAscending else Qt.DescendingOrder)

        for col, key in enumerate(columns):
            values = table[key]
            notEditable = key in self.DEFAULT['notEditableColumn']
            for row, spotIdx in enumerate(order):
                item = self.infoTable.item(row, col)
                if item is None:
                    item = QTableWidgetItem()
                    self.infoTable.setItem(row, col, item)
                item.setText(str(values[spotIdx]))
                if notEditable:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QColor('lightgray'))
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

        if 'color' in columns:
            colorCol = columns.index('color')
            for row, spotIdx in enumerate(order):
                self.infoTable.item(row, colorCol).setBackground(
                    QColor(table['color'][spotIdx]))

        self.infoTable.blockSignals(False)

    def updateSelect(self,idx):
        logger.debug(f'row to select : {idx}')

        idx = np.array(idx, ndmin=1)
        order = self._displayOrder()   # order[row] = spot index shown there
        rowOfSpot = {spotIdx: row for row, spotIdx in enumerate(order)}

        self.infoTable.selectionModel().clear()
        self.infoTable.setSelectionMode(QAbstractItemView.MultiSelection)
        for ii in idx:
            if ii is not None and ii in rowOfSpot:
                self.infoTable.selectRow(rowOfSpot[ii])
        self.infoTable.setSelectionMode(QAbstractItemView.ExtendedSelection)

if __name__ == "__main__":
    pass

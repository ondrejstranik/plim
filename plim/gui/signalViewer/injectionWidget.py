'''
class for viewing info about injection of solutions in the sensor
'''

import pyqtgraph as pg
from PyQt5.QtGui import QColor, QPen
from qtpy.QtWidgets import QWidget,QVBoxLayout,QTextEdit, QLabel
from qtpy.QtCore import Signal, Qt
from magicgui import magicgui

import numpy as np


class InjectionWidget(QWidget):
    ''' main class for viewing info about injection into the sensor'''
    DEFAULT = {'nameGUI':'InjectionInfo'}

    sigUpdateData = Signal()

    def __init__(self, injectionData = None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        #self.injectionData = injectionData if injectionData is not None else None
        infoBox = None

        # set this gui of this class
        InjectionWidget._setWidget(self)


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

        @magicgui(auto_call=True)
        def infoBox(number: int = 0):

            # emit signal to eventually update data in other guis
            self.sigUpdateData.emit()


        # Zentrales Widget und Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Textfeld (Editor)
        self.editor = QTextEdit()
        layout.addWidget(self.editor)

        # Statusanzeige für Cursor-Position
        self.status_label = QLabel("Zeile: 1, Spalte: 0")
        layout.addWidget(self.status_label)

        # infoBox
        self.infoBox = infoBox
        layout.addWidget(self.infoBox.native)


        # Event: Cursor-Position überwachen
        self.editor.cursorPositionChanged.connect(self.update_cursor_info)

    def update_cursor_info(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()
        self.status_label.setText(f"Zeile: {line}, Spalte: {col}")



if __name__ == "__main__":
    pass

        















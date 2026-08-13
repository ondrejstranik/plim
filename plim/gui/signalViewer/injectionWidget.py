'''
class for viewing info about injection of solutions in the sensor
'''

import time

from qtpy.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTextEdit, QPushButton, QLineEdit
from qtpy.QtCore import Signal

from plim.algorithm.injectionData import InjectionData


class InjectionWidget(QWidget):
    ''' main class for viewing info about injection into the sensor'''
    DEFAULT = {'nameGUI':'InjectionInfo'}

    sigUpdateData = Signal()

    def __init__(self, injectionData = None, **kwargs):
        ''' initialise the class '''
        super().__init__()

        # define the data
        self.iD = injectionData if injectionData is not None else InjectionData()

        # set this gui of this class
        InjectionWidget._setWidget(self)


    def _setWidget(self):
        ''' prepare the gui '''

        # Zentrales Widget und Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Textfeld (Editor)
        self.editor = QTextEdit()
        layout.addWidget(self.editor)

        if self.iD.data:
            # show the already existing data
            self.editor.setPlainText(self.iD.data)
        else:
            self.iD.setData(self._makeTimeTagLine(0) + '\n')
            self.editor.setPlainText(self.iD.data)

        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.End)
        self.editor.setTextCursor(cursor)

        # keep injectionData in sync with the editor content
        self.editor.textChanged.connect(self.updateData)

        # time tag: input box for the relative time + button to insert the tag
        timeTagLayout = QHBoxLayout()
        self.timeInput = QLineEdit()
        self.timeInput.setText("0")
        self.addTimeTagButton = QPushButton("add time tag")
        self.addTimeTagButton.clicked.connect(self.addTimeTag)
        self.addNowTimeTagButton = QPushButton("now")
        self.addNowTimeTagButton.clicked.connect(self.addNowTimeTag)
        timeTagLayout.addWidget(self.timeInput)
        timeTagLayout.addWidget(self.addTimeTagButton)
        timeTagLayout.addWidget(self.addNowTimeTagButton)
        layout.addLayout(timeTagLayout)

    def _makeTimeTagLine(self, relativeTime):
        ''' format a time tag line for the given relative time (in s) '''
        relativeTime = int(float(relativeTime))
        absoluteTimeNs = int(self.iD.time0 + relativeTime * 1e9)
        return f'#%% {relativeTime} s ({absoluteTimeNs} ns)'

    def _makeTimeTagLineNow(self):
        ''' format a time tag line for the actual (current) time '''
        absoluteTimeNs = int(time.time() * 1e9)
        relativeTime = int((absoluteTimeNs - self.iD.time0) / 1e9)
        return f'#%% {relativeTime} s ({absoluteTimeNs} ns)'

    def _insertLine(self, line):
        ''' insert a line on a new line below the cursor '''
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.EndOfLine)
        cursor.insertBlock()
        cursor.insertText(line)
        cursor.insertBlock()

        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def updateData(self):
        ''' keep injectionData in sync with the editor content '''
        self.iD.setData(self.editor.toPlainText())

        # emit signal to eventually update data in other guis
        self.sigUpdateData.emit()

    def addTimeTag(self):
        ''' insert a time tag on a new line below the cursor, using the relative time from the input box '''
        self._insertLine(self._makeTimeTagLine(self.timeInput.text()))

    def addNowTimeTag(self):
        ''' insert a time tag on a new line below the cursor, using the actual (current) time '''
        self._insertLine(self._makeTimeTagLineNow())



if __name__ == "__main__":
    pass

        















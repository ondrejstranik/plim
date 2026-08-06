'''
script to run analysis of plasmon signals
'''
#%%
from qtpy.QtWidgets import QApplication
import sys
from plim.gui.signalAnalyser.signalAnalyser import SignalAnalyser

def main():
    app = QApplication([])
    window = SignalAnalyser()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    
#%%


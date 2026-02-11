''' camera unitest '''

import pytest


def test_regloICC():
    ''' check if pump is working'''
    from plim.instrument.pump.regloICC import RegloICC
    import time

    RegloICC.DEFAULT['serialNo'] = 'H21002980'
    pump = RegloICC()
    pump.connect()
    pump._setFlowRate(10)    
    pump._setFlow(True)
    time.sleep(3)
    pump._setFlowRate(-10)
    time.sleep(3)
    pump._setFlowRate(0)
    pump.disconnect()

def test_regloICC_GUI():
    ''' check if reglopump works with gui'''
    from viscope.main import viscope
    from viscope.gui.pumpGUI import PumpGUI   
    from plim.instrument.pump.regloICC import RegloICC

    RegloICC.DEFAULT['serialNo'] = 'H21002980'
    pump = RegloICC()
    pump.connect()

    viewer  = PumpGUI(viscope)
    viewer.setDevice(pump)
    viscope.run()

    pump.disconnect()
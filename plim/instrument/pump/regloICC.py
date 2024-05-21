"""
Pump Reglo ICC from Ismatec

Created on Mon Nov 15 12:08:51 2021

@author: ostranik
"""
#%%

import os
import time
import numpy as np
from viscope.instrument.base.basePump import BasePump

import serial

class RegloICC(BasePump):
    ''' class to control reglo ICC pump'''
    DEFAULT = {'name': 'RegloICC',
                'serialNo': '0922001142',
                'port': 'COM4',
                'channel': 4 # from 1 to 4
    }

    def __init__(self, name=None,**kwargs):
        ''' initialisation '''

        if name is None: name=RegloICC.DEFAULT['name'] 
        super().__init__(name=name,**kwargs)

        self._device = None
        self._port= kwargs['port'] if 'port' in kwargs else RegloICC.DEFAULT['port']
        self.serialNo= kwargs['serialNo'] if 'serialNo' in kwargs else RegloICC.DEFAULT['serialNo']
        self.channel= kwargs['channel'] if 'channel' in kwargs else RegloICC.DEFAULT['channel']

    def _open(self):
        ''' try to open serial port and check the serial number '''
        # make three attempts 
        for i in range(3):
            try:  
                self._device = serial.Serial(self._port, timeout=1)
                serialnb = self._cmd('1xS', 9, False)
                self._cmd('1~0', '*')
                self._cmd('1xE0', '*')
                self._cmd('1D'+  'viscope', '*')
                self._cmd('1M', '*')
                self._cmd('1~1', '*')
                if serialnb == self.serialNo:
                    print(self.name + 'pump with serialNo --' + str(self.serialNo) + '-- opened')
                    return
                else:
                    print('serial number wrong: ' + str(serialnb) + '!=' + str(self.serialNo))
                    break
            except serial.SerialException:
                print(self.name + ' serial.SerialException')
            time.sleep(0.5)
        print(self.name + ' not able to open pump')

    def _cmd(self, command, response=None, reopen=True):
        ''' send command on the pump via serial port '''
        command = str(command) + '\r\n'       # unterschiedliche rückgabewerte,
        for i in range(3):
            try:                                  # je nach übergabe 'response'
                self._device.reset_input_buffer()
                self._device.write(command.encode())     # senden
                if response is None:
                    return 0
                if type(response) is int:
                    return self._device.read(response + 1).decode().strip()
                if type(response) is str:
                    res = self._device.read(len(response))
                    if res == response.encode():
                        return 0
            except (serial.SerialException, serial.serialutil.SerialTimeoutException):
                if reopen:
                    self._device.close()
                    self._open()
            print(self.name + ' serial cmd error')
            time.sleep(0.5)
        print(self.name + ' serial cmd error, command: ' + str(command))
        return 0

    def _stop(self):
        self._cmd('1~0', reopen=False)
        self._cmd('1I', reopen=False)

    def connect(self):
        self._open()
        super().connect()

    def disconnect(self):
        self._stop()
        self._device.close()
        super().disconnect()

    def _setFlowRate(self,value):
        ''' set flow rate of the channel '''
        super()._setFlowRate(value)
        if self.flow:
            self._stop()
            if self.flowRate > 0:
                self._cmd('1~1')
                self._cmd(str(self.channel) +'K')
                _frString = (f'{int(self.flowRate*10**(3-int(np.log10(self.flowRate))))}' +
                             f'-{(3-int(np.log10(self.flowRate)))}')
                self._cmd(str(self.channel) + 'f' + _frString)
                self._cmd(str(self.channel) +'H')
                #print(str(self.channel) + 'f' + _frString)

            if self.flowRate < 0:
                self._cmd('1~1')
                self._cmd(str(self.channel) +'J')
                _frString = (f'{int(-self.flowRate*10**(3-int(np.log10(-self.flowRate))))}' +
                             f'-{(3-int(np.log10(-self.flowRate)))}')
                self._cmd(str(self.channel) + 'f' + _frString)
                self._cmd(str(self.channel) +'H')
                #print(str(self.channel) + 'f' + _frString)


            #print(f'from flowRate: flowRate = {self.flowRate*self.flow}')

    def _setFlow(self,value):
        ''' set if channel should flow or not '''
        super()._setFlow(value)

        if self.flow:
            self.setParameter('flowRate',self.flowRate)
        else:
            self._stop()           

        #print(f'from flow: flowRate = {self.flowRate*self.flow}')


#%%

if __name__ == '__main__':
    pass
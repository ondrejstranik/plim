'''
class for calculating spot spectra from 3D spectral cube
'''
#%%
import numpy as np
import time


class SpotData:
    ''' class for processing signal from spots '''
    DEFAULT = {}


    def __init__(self,signal=None,time=None,**kwarg):
        ''' initialization of the parameters '''
        #TODO: implement signal and time definition for a single values. 

        self.signal = None # numpy array, each column represent signal from one spot
        self.time = None # corresponding time
        self.time0 = 0 # position of zero time

        # values from the data
        self.offset = None
        self.alignTime = 0
        self.range = 2
        self.evalTime = 0
        self.dTime = 1
        self.dSignal = None

        if signal is not None: self.setData(signal,time)

        # color for each signal
        self.signalColor = None
        # info for each signal
        # TODO: implement the signalInfo
        self.signalInfo = None

    def setData(self,signal,time=None):
        ''' set signal and (time)'''
        self.signal = np.array(signal)
        self.time = np.array(time) if time is not None else np.arange(self.signal.shape[0])  # corresponding time
        self.time0 = self.time[0]
        self.setOffset()


    def addDataValue(self, valueVector,time= None):
        ''' add single value to the signal
            return time0 if data are reset'''
        
        valueVector = np.array(valueVector)
        if self.signal is not None and valueVector.shape[0] == self.signal.shape[1]:
            self.signal = np.vstack((self.signal,valueVector))
            if time is not None: self.time = np.append(self.time,time)
            return None
        else:
            self.signal = np.array(valueVector)[None,:]
            if time is not None: 
                self.time = np.array(time)[None]
                self.time0 = self.time[0] # reset time0
            else:
                self.time0 = 0
            return self.time0
                
    def getData(self):
        ''' return the signal and time '''
        if self.signal is not None:
            if (hasattr(self,'time')  and self.signal.shape[0] == self.time.shape[0]):
                return (self.signal,self.time-self.time0)
            else:
                return (self.signal,np.arange(self.signal.shape[0]))
        else:
            return (None, None)


    def setOffset(self, alignTime=None, range= None):
        ''' set offset value for the signal at the time offsetTime'''

        if alignTime is not None: self.alignTime = alignTime
        if range is not None: self.range = range

        print(f't0 {self.time - self.time0 - self.alignTime - self.range/2}')
        print(f't1 {self.time - self.time0 - self.alignTime + self.range/2}')


        range = np.all((self.time - self.time0 - self.alignTime - self.range/2)>=0,
                 (self.time - self.time0 - self.alignTime + self.range/2)<=0)
        
        self.offset = np.mean(self.signal[range,:],axis=0)

    def getDSignal(self,evalTime=None,dTime=None, range=None):
        ''' get the difference value of signal'''

        if evalTime is not None: self.evalTime = evalTime
        if dTime is not None: self.dTime = dTime
        if range is not None: self.range = range

        range = np.all((self.time - self.time0 - self.evalTime - self.range/2)>=0,
                 (self.time - self.time0 - self.evalTime + self.range/2)<=0)
        _signal1 = np.mean(self.signal[range,:],axis=0)
        range = np.all((self.time - self.time0 - self.evalTime - self.dTime - self.range/2)>=0,
                 (self.time - self.time0 - self.evalTime -self.dTime + self.range/2)<=0)
        _signal2 = np.mean(self.signal[range,:],axis=0)


        self.dSignal = _signal2 - _signal1

        return self.dSignal


        

                 





    def clearData(self):
        ''' clear the data '''
        self.signal = None
        self.time = None
        self.time0 = 0

        
#%%

if __name__ == "__main__":
    pass
















# %%

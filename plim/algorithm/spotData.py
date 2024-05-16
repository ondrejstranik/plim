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
        
        if signal is not None: self.signal = np.array(signal)  # position of plasmon peaks 
        if time is not None: self.time = np.array(time) # corresponding time


    def setData(self,signal,time=None):
        ''' set signal and (time)'''
        self.signal = np.array(signal)
        self.time = np.array(time) if time is not None else np.arange(self.signal.shape[0])  # corresponding time       

    def addDataValue(self, valueVector,time= None):
        ''' add single value to the signal'''
        
        valueVector = np.array(valueVector)
        if self.signal is not None and valueVector.shape[0] == self.signal.shape[1]:
            self.signal = np.vstack((self.signal,valueVector))
            if time is not None: self.time = np.append(self.time,time)
        else:
            self.signal = np.array(valueVector)[None,:]
            if time is not None: self.time = np.array(time)[None]

    def getData(self):
        ''' return the signal and time '''
        if self.signal is not None:
            if (hasattr(self,'time')  and self.signal.shape[0] == self.time.shape[0]):
                return (self.signal,self.time-self.time[0])
            else:
                return (self.signal,np.arange(self.signal.shape[0]))
        else:
            return (None, None)

        
#%%

if __name__ == "__main__":
    pass
















# %%

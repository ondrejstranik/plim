'''
class for processing info about injection
'''
#%%
import numpy as np
import time


class InjectionData:
    ''' class for processing info about injection '''
    DEFAULT = {}


    def __init__(self,data=None,time0=None,**kwarg):
        ''' initialization of the parameters '''

        self.data = ''
        self.time0 = time.time_ns() #  time in ns from the start of Epoch

        if data is not None: self.data = data
        if time0 is not None: self.time0 = time0 # same as in spotData

    def setData(self,data,time0=None):
        ''' set signal and (time)'''
        self.data = data
        if time0 is not None: self.time0 = time0

    def setT0(self,value):
        ''' set the initial time '''
        self.time0 = value

    def clearData(self):
        ''' clear the data '''
        self.data = ''
        self.time0 = time.time_ns() #  time in ns from the start of Epoch

        
#%%

if __name__ == "__main__":
    pass
















# %%

'''
class for info about spots
'''
#%%
import numpy as np
import time


class SpotInfo:
    ''' class for info about spots '''
    DEFAULT = {'n':5}


    def __init__(self,**kwarg):
        ''' initialization of the parameters '''

        self.nSpot = SpotInfo.DEFAULT['n']

        self.table = {
            'name': ['default Name' for x in range(self.nSpot)],
            'color': ['default Color' for x in range(self.nSpot)],
            'visible': [True for x in range(self.nSpot)]
        }


        
#%%

if __name__ == "__main__":
    pass
















# %%

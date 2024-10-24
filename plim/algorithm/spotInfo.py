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

        self.name = self.nSpot*['default Name']
        self.color = self.nSpot*['default Color']
        self.visible = self.nSpot*True

        
#%%

if __name__ == "__main__":
    pass
















# %%

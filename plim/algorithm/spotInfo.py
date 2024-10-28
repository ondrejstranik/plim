'''
class for info about spots
'''
#%%
import numpy as np
import time


class SpotInfo:
    ''' class for info about spots '''
    DEFAULT = {'n':5}


    def __init__(self,n=None, **kwarg):
        ''' initialization of the parameters '''

        
        self.nSpot = n if n is not None else SpotInfo.DEFAULT['n']

        self.table = {
            'name': [str(x) for x in range(self.nSpot)],
            'color': ['#ffffff' for x in range(self.nSpot)],
            'visible': ['True' for x in range(self.nSpot)]
        }

    def checkValues(self):
        print('checkTypes')
        self.table['visible'] = [
            'True' if x.lower() in ("true", "1") else 'False' for x in self.table['visible']
            ]

        
#%%

if __name__ == "__main__":
    pass
















# %%

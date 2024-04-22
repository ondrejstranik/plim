'''
class for live viewing spectral images
'''
#%%

#import numpy as np
from viscope.main import Viscope 


class Plim():
    ''' base top class for control'''

    DEFAULT = {}

    def __init__(self, **kwargs ):
        ''' initialise the class '''

        self.viscope = Viscope(name='plim')


    def run(self):
        '''  run the GUI'''
        
        self.viscope.run()

if __name__ == "__main__":

        plim = Plim()
        plim.run()


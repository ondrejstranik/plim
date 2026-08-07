'''
base package  

'''


# trick how to make variable global 
#import __main__
#testVar = 'ahoj'
#_main__.testVar = testVar

from pathlib import Path
dataFolder = Path(Path(__file__).parent.joinpath('DATA'))
"""Path to the package's local DATA folder, created on import if missing."""
dataFolder.mkdir(parents=True, exist_ok=True)
dataFolder = str(dataFolder)


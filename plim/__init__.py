# trick how to make variable global 
#import __main__
#testVar = 'ahoj'
#_main__.testVar = testVar

from pathlib import Path
dataFolder = Path(Path(__file__).parent.joinpath('DATA'))
# generate folder if it does not exist
dataFolder.mkdir(parents=True, exist_ok=True)
dataFolder = str(dataFolder)

